"""Coleta QML limitada ao assistente e ao estilo Basic."""
from pathlib import Path
from PyInstaller.utils.hooks.qt import add_qt6_dependencies, pyside6_library_info

hiddenimports, binaries, datas = add_qt6_dependencies(__file__)
qml_binaries, qml_datas = pyside6_library_info.collect_qtqml_files()
allowed = {'QtQml', 'QtQml/Models', 'QtQml/WorkerScript', 'QtQml/Meta',
           'QtQuick', 'QtQuick/Window', 'QtQuick/Layouts', 'QtQuick/Templates',
           'QtQuick/Controls', 'QtQuick/Controls/impl', 'QtQuick/Controls/Basic',
           'QtQuick/Controls/Basic/impl', 'QtQuick/Effects', 'QtQuick/Shapes',
           'Qt/labs/qmlmodels'}
root = Path(pyside6_library_info.location['QmlImportsPath']).resolve()

def selected(pair):
    source = Path(pair[0]).resolve()
    parent = source if source.is_dir() else source.parent
    while parent != root and root in parent.parents:
        if (parent / 'qmldir').is_file():
            return parent.relative_to(root).as_posix() in allowed
        parent = parent.parent
    return False

binaries += [entry for entry in qml_binaries if selected(entry)]
datas += [entry for entry in qml_datas if selected(entry)]
