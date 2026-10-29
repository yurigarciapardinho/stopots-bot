from dataclasses import replace
import hashlib
import json
import time
import uuid

from .domain import Context, Phase


class ContextTracker:
    """Não usa letra nem relógio como identidade de rodada."""

    def __init__(self, session_id=None, clock=time.monotonic):
        self.context = Context(session_id or uuid.uuid4().hex)
        self.clock = clock
        self.room_key = None
        self.previous_phase = Phase.UNKNOWN
        self.previous_round = None
        self.previous_review = None
        self.fingerprint = None
        self.field_signature = None
        self.stable_since = clock()
        self.seq = 0
        self.in_lobby = False

    def invalidate(self):
        self.context = replace(self.context, room_epoch=self.context.room_epoch + 1,
                               ui_revision=self.context.ui_revision + 1)
        self.previous_phase = Phase.UNKNOWN
        self.previous_review = self.previous_round = self.fingerprint = None
        self.field_signature = None
        self.stable_since = self.clock()
        self.in_lobby = False

    def update(self, raw):
        phase = Phase(raw["phase"])
        room = raw.get("room_key")
        c = self.context
        if room and room != self.room_key:
            c = replace(c, room_epoch=c.room_epoch + 1, match_epoch=0, round_epoch=0)
            self.room_key = room
            self.previous_round = self.previous_review = None
        if phase in (Phase.HOME, Phase.ENTERING) and self.previous_phase not in (Phase.HOME, Phase.ENTERING, Phase.UNKNOWN):
            c = replace(c, room_epoch=c.room_epoch + 1)
            self.room_key = None
        playing = (Phase.COUNTDOWN, Phase.WRITING, Phase.REVIEW, Phase.ROUND_RESULT, Phase.FINAL_RESULT)
        if phase == Phase.ROOM:
            self.in_lobby = True
        if phase in playing and (self.in_lobby or c.match_epoch == 0):
            c = replace(c, match_epoch=c.match_epoch + 1)
            self.in_lobby = False
            self.previous_round = self.previous_review = None
        index = raw.get("round_index")
        round_key = (index, raw.get("letter"))
        new_writing = phase == Phase.WRITING and self.previous_phase in (Phase.ROUND_RESULT, Phase.FINAL_RESULT)
        if phase == Phase.WRITING and (round_key != self.previous_round or new_writing):
            c = replace(c, round_epoch=c.round_epoch + 1)
            self.previous_round = round_key
            self.previous_review = None
        review_index = raw.get("review_index") if phase == Phase.REVIEW else None
        review_key = (review_index, raw.get("review_theme"))
        if phase == Phase.REVIEW and review_key != self.previous_review:
            c = replace(c, review_epoch=c.review_epoch + 1)
            self.previous_review = review_key
        relevant = (phase, index, raw.get("letter"), raw.get("review_theme"), review_index,
                    [(f["ref"], f["label"], f.get("max_length")) for f in raw.get("fields", [])],
                    [(g["ref"], g["text"]) for g in raw.get("groups", [])], raw.get("rules", {}))
        fingerprint = hashlib.sha256(json.dumps(relevant, sort_keys=True).encode()).hexdigest()
        if fingerprint != self.fingerprint:
            c = replace(c, ui_revision=c.ui_revision + 1)
            self.fingerprint = fingerprint
        c = replace(c, round_index=index, review_index=review_index)
        signature = (c.room_epoch, c.match_epoch, c.round_epoch, phase,
                     tuple((f["ref"], f["label"]) for f in raw.get("fields", [])))
        if signature != self.field_signature:
            self.field_signature, self.stable_since = signature, self.clock()
        stable = (phase == Phase.WRITING and bool(raw.get("fields"))
                  and all(f["label"] for f in raw["fields"]) and index is not None
                  and bool(raw.get("letter")) and self.clock() - self.stable_since >= 1.2)
        self.context, self.previous_phase = c, phase
        self.seq += 1
        return c, self.seq, stable
