import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: win
    title: "StopotS Assistente " + backend.product.version
    visible: true
    property bool compact: false
    property int tab: 0
    property int entryMode: 0
    property int passwordChoice: -1
    property bool revealPassword: false
    property string handledEntryError: ""
    property bool dark: backend.preferences.theme === "escuro" || (backend.preferences.theme === "sistema" && backend.systemDark)
    property color bg: dark ? "#20282c" : "#f4f2ed"
    property color surface: dark ? "#2b353b" : "#fffdf8"
    property color ink: dark ? "#eef3f2" : "#233239"
    property color muted: dark ? "#b7c4c7" : "#52636a"
    property color accent: dark ? "#79d1d6" : "#176678"
    property color accentInk: dark ? "#163136" : "#ffffff"
    property color line: dark ? "#536268" : "#b7c5c6"
    width: compact ? 380 : 940
    height: compact ? 580 : 730
    minimumWidth: compact ? 340 : 760
    minimumHeight: compact ? 420 : 520
    color: bg
    onClosing: function(close) { close.accepted=backend.state.can_exit; if(!close.accepted) backend.shutdown(false); }
    Connections {
        target: backend
        function onSessionReady() { win.compact=true; }
        function onChanged() {
            const code=backend.state.error_code || "";
            const fresh=code!==win.handledEntryError;
            win.handledEntryError=code;
            if(fresh && (code === "PASSWORD_REQUIRED" || code === "PASSWORD_REJECTED")) {
                win.compact=false;win.tab=0;win.entryMode=1;win.passwordChoice=1;
            }
        }
    }
    Shortcut { sequence: "Ctrl+P"; onActivated: backend.command(backend.state.active ? "pause" : "resume"); }
    Shortcut { sequence: "Ctrl+,"; onActivated: {win.compact=false;win.tab=1;} }
    Shortcut { sequence: "Ctrl+I"; onActivated: {win.compact=false;about.open();} }
    Dialog {
        id: about
        objectName: "aboutDialog"
        anchors.centerIn: parent
        width: Math.min(win.width-32,620)
        modal: true
        title: "StopotS Assistente " + backend.product.version
        standardButtons: Dialog.Ok
        palette.windowText: win.ink
        palette.text: win.ink
        palette.buttonText: win.ink
        palette.button: win.surface
        background: OrganicPanel {fillColor:win.surface;borderColor:win.line}
        contentItem: ColumnLayout {
            spacing: 14
            LabelText { text: "Projeto de " + backend.product.author; font.bold:true; Layout.fillWidth:true }
            LabelText { text: backend.product.credits; Layout.fillWidth:true }
            HelpText { text: backend.product.license; Layout.fillWidth:true }
            HelpText { text: "Textos completos e fontes: pasta legal da distribuição e documentação de licenciamento."; Layout.fillWidth:true }
            HelpText { text: backend.product.url; Layout.fillWidth:true }
        }
    }

    component LabelText: Text {
        color: win.ink
        font.pixelSize: 16
        wrapMode: Text.WordWrap
        textFormat: Text.PlainText
    }
    component HelpText: LabelText { color: win.muted; font.pixelSize: 14 }
    component SoftButton: Button {
        id: b
        property bool primary: false
        implicitHeight: 48
        implicitWidth: Math.max(100,contentItem.implicitWidth+36)
        hoverEnabled: true
        Accessible.name: text
        background: OrganicPanel {
            fillColor: b.primary ? (b.down ? Qt.darker(win.accent,1.1) : win.accent) : (b.hovered ? (win.dark ? "#3a484f" : "#e4ecea") : win.surface)
            borderColor: b.activeFocus ? win.accent : (b.primary ? "transparent" : win.line)
            opacity: b.enabled ? 1 : .48
        }
        contentItem: Text { text:b.text; color:b.primary ? win.accentInk : win.ink; font.pixelSize:15; font.bold:b.primary; horizontalAlignment:Text.AlignHCenter; verticalAlignment:Text.AlignVCenter; textFormat:Text.PlainText; wrapMode:Text.WordWrap }
    }
    component EntryField: TextField {
        id: f
        implicitHeight: 48
        color: win.ink
        font.pixelSize: 16
        padding: 14
        selectByMouse: true
        placeholderTextColor: win.muted
        selectionColor: win.accent
        selectedTextColor: win.accentInk
        background: OrganicPanel { fillColor:win.surface; borderColor:f.activeFocus ? win.accent : win.line }
    }
    component SectionTitle: LabelText { font.pixelSize:24; font.bold:true }
    component ProfilePicker: ComboBox {
        id: picker
        model: ["Só preencher","Só observar","Automático","Personalizado"]
        currentIndex: Math.max(0, model.indexOf(backend.preferences.profile))
        implicitHeight:48
        Accessible.name: "Perfil de ajuda"
        onActivated: backend.setProfile(currentText)
        background: OrganicPanel {fillColor:win.surface;borderColor:picker.activeFocus ? win.accent : win.line}
        contentItem: LabelText {text:picker.displayText;leftPadding:16;rightPadding:30;verticalAlignment:Text.AlignVCenter}
        indicator: Text {text:"⌄";color:win.muted;font.pixelSize:22;anchors.right:parent.right;anchors.rightMargin:16;anchors.verticalCenter:parent.verticalCenter}
        delegate: ItemDelegate { width:picker.width; text:modelData; highlighted:picker.highlightedIndex===index }
    }
    component ActionRow: RowLayout {
        property string label
        property string actionKey
        property string explanation
        spacing:16
        ColumnLayout {
            Layout.fillWidth:true
            LabelText {text:parent.parent.label;Layout.fillWidth:true}
            HelpText {text:parent.parent.explanation;Layout.fillWidth:true}
        }
        Switch {
            id: toggle
            checked: Boolean(backend.preferences.policy[parent.actionKey])
            onToggled: backend.setAction(parent.actionKey,checked)
            Accessible.name: parent.label
            indicator: OrganicPanel {
                implicitWidth:54;implicitHeight:32
                fillColor:toggle.checked ? win.accent : (win.dark ? "#657278" : "#91a0a5")
                borderColor:toggle.activeFocus ? win.ink : "transparent"
                OrganicPanel {x:toggle.checked?26:4;y:4;width:24;height:24;fillColor:toggle.checked?win.accentInk:win.surface;softness:.2}
            }
        }
    }

    ColumnLayout {
        anchors.fill:parent
        anchors.margins:win.compact?18:24
        spacing:16
        RowLayout {
            Layout.fillWidth:true
            OrganicPanel {
                Layout.preferredWidth:42;Layout.preferredHeight:42;fillColor:win.accent
                Text {anchors.centerIn:parent;text:"S";font.bold:true;font.pixelSize:29;color:win.accentInk}
            }
            ColumnLayout {
                Layout.fillWidth:true;spacing:2
                LabelText {text:"StopotS";font.pixelSize:22;font.bold:true}
                HelpText {text:win.compact?"Assistente local":"Sua ajuda, do seu jeito."}
            }
            SoftButton {text:"Sobre";visible:!win.compact;implicitWidth:90;onClicked:about.open()}
            SoftButton {text:win.compact?"Expandir":"Recolher";implicitWidth:100;onClicked:win.compact=!win.compact}
        }

        RowLayout {
            visible:!win.compact
            Layout.fillWidth:true
            Repeater {
                model:["Jogar","Sua ajuda","Aparência","Atividade"]
                SoftButton {required property int index;required property string modelData;text:modelData;primary:win.tab===index;Layout.fillWidth:true;onClicked:win.tab=index}
            }
        }

        OrganicPanel {
            Layout.fillWidth:true
            Layout.preferredHeight:statusColumn.implicitHeight+36
            visible:win.compact || backend.state.connected || backend.state.busy || backend.state.error_code.length>0
            fillColor:win.surface
            ColumnLayout {
                id:statusColumn
                anchors.fill:parent;anchors.margins:18;spacing:6
                LabelText {text:backend.state.closing?"Encerrando a ajuda…":backend.state.message;Layout.fillWidth:true;font.bold:true;font.pixelSize:18;Accessible.role:Accessible.StaticText}
                HelpText {text:backend.state.detail;Layout.fillWidth:true}
                HelpText {visible:backend.state.applying;text:"Aplicando ajustes às próximas ações…";color:win.accent;Layout.fillWidth:true}
            }
        }

        ScrollView {
            id:scroll
            Layout.fillWidth:true
            Layout.fillHeight:true
            Layout.minimumHeight:0
            Layout.preferredHeight:0
            clip:true
            contentWidth:availableWidth
            ColumnLayout {
                width:scroll.availableWidth
                spacing:16

                ColumnLayout {
                    visible:win.compact
                    Layout.fillWidth:true
                    spacing:16
                    HelpText {text:"Perfil de ajuda"}
                    ProfilePicker {Layout.fillWidth:true}
                    RowLayout {
                        Layout.fillWidth:true
                        OrganicPanel {
                            Layout.fillWidth:true;Layout.preferredHeight:90;fillColor:win.surface
                            Column {anchors.centerIn:parent;spacing:6
                                HelpText {text:"RODADA"}
                                LabelText {text:backend.state.round;font.pixelSize:24;font.bold:true}
                            }
                        }
                        OrganicPanel {
                            Layout.fillWidth:true;Layout.preferredHeight:90;fillColor:win.surface
                            Column {anchors.centerIn:parent;spacing:6
                                HelpText {text:"LETRA"}
                                LabelText {text:backend.state.letter;font.pixelSize:24;font.bold:true}
                            }
                        }
                    }
                    LabelText {visible:backend.state.total>0;text:backend.state.filled+" / "+backend.state.total+" campos com resposta";Layout.fillWidth:true}
                    ProgressBar {visible:backend.state.total>0;value:backend.state.total?backend.state.filled/backend.state.total:0;Layout.fillWidth:true;Accessible.name:"Campos com resposta"}
                    HelpText {text:backend.state.pending.length?"Precisam de você: "+backend.state.pending.join(", "):"STOP, votos e avanço seguem o perfil escolhido.";Layout.fillWidth:true}
                }

                GridLayout {
                    visible:!win.compact && win.tab===0
                    Layout.fillWidth:true;columns:2;columnSpacing:28;rowSpacing:16
                    SectionTitle {text:"Vamos jogar";Layout.columnSpan:2}
                    ColumnLayout {
                        Layout.preferredWidth:270;Layout.minimumWidth:230;Layout.maximumWidth:300;Layout.alignment:Qt.AlignTop;spacing:16
                        SoftButton {text:"Escolher no jogo";primary:win.entryMode===0;Layout.fillWidth:true;onClicked:win.entryMode=0}
                        SoftButton {text:"Entrar por convite";primary:win.entryMode===1;Layout.fillWidth:true;onClicked:win.entryMode=1}
                        HelpText {text:"Perfil de ajuda"}
                        ProfilePicker {Layout.fillWidth:true}
                        HelpText {text:backend.preferences.profile==="Só preencher"?"Preenche vazios. STOP, votos e avanço ficam com você.":"Confira as permissões em Sua ajuda.";Layout.fillWidth:true}
                        SoftButton {visible:win.entryMode===0;text:"Iniciar ajuda e abrir jogo";primary:true;Layout.fillWidth:true;enabled:!backend.state.busy;onClicked:backend.command("start")}
                        HelpText {text:"O Chrome fica aberto quando a partida termina ou você fecha o assistente.";Layout.fillWidth:true}
                    }
                    ColumnLayout {
                        visible:win.entryMode===1;Layout.fillWidth:true;Layout.alignment:Qt.AlignTop;spacing:10
                        LabelText {text:"Link do convite"}
                        EntryField {id:inviteUrl;objectName:"inviteUrl";Layout.fillWidth:true;placeholderText:"https://stopots.com/pt/08193";Accessible.name:"Link do convite"}
                        LabelText {text:"Seu apelido"}
                        EntryField {id:nick;objectName:"nickname";Layout.fillWidth:true;text:backend.preferences.nickname;maximumLength:15;Accessible.name:"Seu apelido"}
                        LabelText {text:"A sala tem senha?"}
                        RowLayout {
                            Layout.fillWidth:true
                            SoftButton {text:"Não";primary:win.passwordChoice===0;Layout.fillWidth:true;onClicked:{win.passwordChoice=0;secret.clear();}}
                            SoftButton {text:"Sim";primary:win.passwordChoice===1;Layout.fillWidth:true;onClicked:win.passwordChoice=1}
                        }
                        ColumnLayout {
                            visible:win.passwordChoice===1;Layout.fillWidth:true
                            LabelText {text:"Senha da sala"}
                            RowLayout {
                                Layout.fillWidth:true
                                EntryField {id:secret;objectName:"roomPassword";Layout.fillWidth:true;Accessible.name:"Senha da sala";echoMode:win.revealPassword?TextInput.Normal:TextInput.Password;onAccepted:enterButton.clicked()}
                                SoftButton {text:win.revealPassword?"Ocultar":"Mostrar";onClicked:win.revealPassword=!win.revealPassword}
                            }
                            HelpText {text:"Usada somente para esta entrada.";Layout.fillWidth:true}
                        }
                        SoftButton {
                            id:enterButton;objectName:"enterInvitation";text:"Entrar com ajuda";primary:true;Layout.fillWidth:true
                            enabled:!backend.state.busy && win.passwordChoice>=0 && inviteUrl.text.length>0 && nick.text.trim().length>0 && (win.passwordChoice===0 || secret.text.length>0)
                            onClicked: {
                                if(!enabled) return;
                                if(backend.state.in_room) replaceDialog.open();
                                else {backend.invite(inviteUrl.text,nick.text,win.passwordChoice===1,secret.text,false);secret.clear();}
                            }
                        }
                    }
                    OrganicPanel {
                        visible:win.entryMode===0;Layout.fillWidth:true;Layout.preferredHeight:240;Layout.alignment:Qt.AlignTop;fillColor:win.surface
                        ColumnLayout {anchors.fill:parent;anchors.margins:24;spacing:16
                            SectionTitle {text:"Você no comando";Layout.fillWidth:true}
                            HelpText {text:"Abra o jogo, escolha uma sala e acompanhe a ajuda no painel compacto.";Layout.fillWidth:true}
                            HelpText {text:"Pausar ajuda mantém a partida aberta. Você pode editar suas respostas a qualquer momento.";Layout.fillWidth:true}
                            Item {Layout.fillHeight:true}
                        }
                    }
                }

                ColumnLayout {
                    visible:!win.compact && win.tab===1
                    Layout.fillWidth:true;spacing:18
                    SectionTitle {text:"Sua ajuda"}
                    ProfilePicker {Layout.fillWidth:true}
                    ActionRow {Layout.fillWidth:true;label:"Preencher campos vazios";actionKey:"fill_blanks";explanation:"Suas respostas e edições são preservadas."}
                    ActionRow {Layout.fillWidth:true;label:"STOP automático";actionKey:"request_stop";explanation:"Aguarda o botão real ficar disponível."}
                    ActionRow {Layout.fillWidth:true;label:"Ajustar votos";actionKey:"set_votes";explanation:"Respostas desconhecidas mantêm o voto atual."}
                    ActionRow {Layout.fillWidth:true;label:"Confirmar AVALIAR";actionKey:"confirm_review";explanation:"Confirma a etapa de apuração."}
                    ActionRow {Layout.fillWidth:true;label:"Avançar entre rodadas";actionKey:"continue_results";explanation:"Continua após o ranking da rodada."}
                    ActionRow {Layout.fillWidth:true;label:"Exigir todos antes de STOP";actionKey:"require_all_filled";explanation:"Política do assistente; a disponibilidade depende do jogo."}
                    HelpText {text:"Ajustes valem para as próximas ações. Ações já enviadas não são desfeitas. Trocar o perfil mantém a pausa.";Layout.fillWidth:true}
                }

                ColumnLayout {
                    visible:!win.compact && win.tab===2
                    Layout.fillWidth:true;spacing:18
                    SectionTitle {text:"Do seu jeito"}
                    HelpText {text:"Superfícies suaves, formas orgânicas e foco no jogo.";Layout.fillWidth:true}
                    Repeater {
                        model:[{label:"Seguir o sistema",value:"sistema"},{label:"Claro",value:"claro"},{label:"Escuro",value:"escuro"}]
                        SoftButton {required property var modelData;text:modelData.label;primary:backend.preferences.theme===modelData.value;Layout.fillWidth:true;onClicked:backend.setTheme(modelData.value)}
                    }
                    CheckBox {text:"Reduzir movimento";checked:backend.preferences.reduced_motion;onToggled:backend.setReducedMotion(checked);palette.windowText:win.ink}
                    HelpText {text:"Atalhos com esta janela em foco: Ctrl+P pausa/retoma a ajuda; Ctrl+, abre os ajustes.";Layout.fillWidth:true}
                }

                ColumnLayout {
                    visible:!win.compact && win.tab===3
                    Layout.fillWidth:true;spacing:12
                    SectionTitle {text:"Acompanhamento"}
                    HelpText {text:"Fase: "+(backend.state.phase || "Aguardando jogo")+" · Rodada: "+backend.state.round+" · Letra: "+backend.state.letter;Layout.fillWidth:true}
                    LabelText {text:backend.state.total?backend.state.filled+" / "+backend.state.total+" campos com resposta":"Aguardando dados da rodada";Layout.fillWidth:true}
                    HelpText {text:backend.state.pending.length?"Sem candidato: "+backend.state.pending.join(", "):"As pendências aparecem aqui durante a rodada.";Layout.fillWidth:true}
                    HelpText {visible:backend.state.ranking.length>0;text:backend.state.ranking_scope==="podium"?"Placar observado: pódio da partida":"Placar observado: linhas visíveis";Layout.fillWidth:true}
                    Repeater {model:backend.state.ranking;LabelText {required property var modelData;text:modelData.player+": "+modelData.points+" pontos";Layout.fillWidth:true}}
                    Repeater {model:backend.state.activity;HelpText {required property string modelData;text:"• "+modelData;Layout.fillWidth:true}}
                    SoftButton {text:"Fechar jogo e aplicativo";Layout.fillWidth:true;onClicked:closeGameDialog.open()}
                }
            }
        }

        RowLayout {
            Layout.fillWidth:true
            SoftButton {text:backend.state.busy?"Cancelar entrada":(backend.state.active?"Pausar ajuda":"Retomar ajuda");primary:true;Layout.fillWidth:true;enabled:!backend.state.closing;onClicked:backend.command(backend.state.busy?"cancel":(backend.state.active?"pause":"resume"))}
            SoftButton {text:"Abrir jogo";Layout.fillWidth:true;enabled:!backend.state.busy && !backend.state.closing;onClicked:backend.command("open")}
        }
    }
    Dialog {
        id:replaceDialog;title:"Trocar de sala?";modal:true;anchors.centerIn:parent;width:Math.min(480,win.width-40);implicitHeight:220
        standardButtons:Dialog.Ok|Dialog.Cancel
        contentItem: Label {text:"Você sairá da sala atual para entrar no convite informado.";wrapMode:Text.WordWrap}
        onAccepted:{backend.invite(inviteUrl.text,nick.text,win.passwordChoice===1,secret.text,true);secret.clear();}
    }
    Dialog {
        id:closeGameDialog;title:"Fechar jogo e aplicativo?";modal:true;anchors.centerIn:parent;width:Math.min(480,win.width-40);implicitHeight:220
        standardButtons:Dialog.Ok|Dialog.Cancel
        contentItem: Label {text:"Esta ação fecha o Chrome dedicado. Para continuar jogando manualmente, feche apenas a janela do assistente pelo X.";wrapMode:Text.WordWrap}
        onAccepted:backend.shutdown(true)
    }
}
