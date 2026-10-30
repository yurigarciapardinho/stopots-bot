import QtQuick
import Stopots.UI 1.0

Item {
    id: panel
    property color fillColor: "#fffdf8"
    property color borderColor: "transparent"
    property real softness: 1
    default property alias contents: body.data
    OrganicSurface {anchors.fill:parent;surfaceColor:panel.fillColor;borderColor:panel.borderColor;softness:panel.softness}
    Item { id: body; anchors.fill: parent }
}
