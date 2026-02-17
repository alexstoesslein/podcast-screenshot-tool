const { app, BrowserWindow, dialog, Menu, shell } = require('electron');
const path = require('path');

let mainWindow;

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1280,
        height: 800,
        minWidth: 800,
        minHeight: 600,
        title: 'Screenshot Tool',
        titleBarStyle: 'hiddenInset',
        trafficLightPosition: { x: 16, y: 16 },
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true
        },
        backgroundColor: '#f5f5f7',
        show: false
    });

    mainWindow.loadFile(path.join(__dirname, 'app', 'index.html'));

    mainWindow.once('ready-to-show', () => {
        mainWindow.show();
    });

    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}

// Menü
const template = [
    {
        label: app.name,
        submenu: [
            { role: 'about', label: 'Über Screenshot Tool' },
            { type: 'separator' },
            { role: 'hide', label: 'Screenshot Tool ausblenden' },
            { role: 'hideOthers', label: 'Andere ausblenden' },
            { role: 'unhide', label: 'Alle einblenden' },
            { type: 'separator' },
            { role: 'quit', label: 'Screenshot Tool beenden' }
        ]
    },
    {
        label: 'Bearbeiten',
        submenu: [
            { role: 'undo', label: 'Rückgängig' },
            { role: 'redo', label: 'Wiederherstellen' },
            { type: 'separator' },
            { role: 'cut', label: 'Ausschneiden' },
            { role: 'copy', label: 'Kopieren' },
            { role: 'paste', label: 'Einfügen' },
            { role: 'selectAll', label: 'Alles auswählen' }
        ]
    },
    {
        label: 'Ansicht',
        submenu: [
            { role: 'reload', label: 'Neu laden' },
            { role: 'toggleDevTools', label: 'Entwicklertools' },
            { type: 'separator' },
            { role: 'resetZoom', label: 'Originalgröße' },
            { role: 'zoomIn', label: 'Vergrößern' },
            { role: 'zoomOut', label: 'Verkleinern' },
            { type: 'separator' },
            { role: 'togglefullscreen', label: 'Vollbild' }
        ]
    },
    {
        label: 'Fenster',
        submenu: [
            { role: 'minimize', label: 'Minimieren' },
            { role: 'zoom', label: 'Zoomen' },
            { role: 'close', label: 'Schließen' }
        ]
    }
];

app.whenReady().then(() => {
    const menu = Menu.buildFromTemplate(template);
    Menu.setApplicationMenu(menu);
    createWindow();
});

app.on('window-all-closed', () => {
    app.quit();
});

app.on('activate', () => {
    if (mainWindow === null) {
        createWindow();
    }
});
