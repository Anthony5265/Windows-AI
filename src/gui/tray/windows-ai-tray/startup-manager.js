/**
 * Windows Startup Manager
 * Manages Windows registry startup entry for Windows AI Tray
 */

const { app } = require('electron');
const path = require('path');
const fs = require('fs');

/**
 * Add Windows AI Tray to Windows startup
 * Uses Windows registry to auto-start on boot
 */
function addToStartup() {
    if (process.platform !== 'win32') {
        console.log('Startup management only available on Windows');
        return false;
    }

    try {
        const Registry = require('winreg');

        const regKey = new Registry({
            hive: Registry.HKCU,
            key: '\\Software\\Microsoft\\Windows\\CurrentVersion\\Run'
        });

        // Get executable path
        const exePath = app.getPath('exe');

        // Add to registry
        regKey.set('WindowsAI', Registry.REG_SZ, `"${exePath}"`, (err) => {
            if (err) {
                console.error('Failed to add to startup:', err);
                return false;
            }
            console.log('✓ Added to Windows startup');
            return true;
        });

    } catch (error) {
        console.error('Error adding to startup:', error);

        // Fallback: Try using PowerShell
        try {
            const { exec } = require('child_process');
            const exePath = app.getPath('exe');

            const ps = `$path = '${exePath}'; $name = 'WindowsAI'; $WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut("$env:APPDATA\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\\$name.lnk"); $Shortcut.TargetPath = $path; $Shortcut.Save()`;

            exec(`powershell -Command "${ps}"`, (err) => {
                if (err) {
                    console.error('PowerShell fallback failed:', err);
                    return false;
                }
                console.log('✓ Added to Windows startup (via PowerShell)');
                return true;
            });
        } catch (psError) {
            console.error('PowerShell fallback error:', psError);
            return false;
        }
    }

    return true;
}

/**
 * Remove Windows AI Tray from Windows startup
 */
function removeFromStartup() {
    if (process.platform !== 'win32') {
        return false;
    }

    try {
        const Registry = require('winreg');

        const regKey = new Registry({
            hive: Registry.HKCU,
            key: '\\Software\\Microsoft\\Windows\\CurrentVersion\\Run'
        });

        regKey.remove('WindowsAI', (err) => {
            if (err) {
                console.error('Failed to remove from startup:', err);
                return false;
            }
            console.log('✓ Removed from Windows startup');
            return true;
        });

    } catch (error) {
        console.error('Error removing from startup:', error);

        // Fallback: Remove shortcut
        try {
            const shortcutPath = path.join(
                process.env.APPDATA,
                'Microsoft',
                'Windows',
                'Start Menu',
                'Programs',
                'Startup',
                'WindowsAI.lnk'
            );

            if (fs.existsSync(shortcutPath)) {
                fs.unlinkSync(shortcutPath);
                console.log('✓ Removed startup shortcut');
                return true;
            }
        } catch (fsError) {
            console.error('Shortcut removal failed:', fsError);
        }

        return false;
    }

    return true;
}

/**
 * Check if Windows AI Tray is in Windows startup
 */
function isInStartup(callback) {
    if (process.platform !== 'win32') {
        callback(false);
        return;
    }

    try {
        const Registry = require('winreg');

        const regKey = new Registry({
            hive: Registry.HKCU,
            key: '\\Software\\Microsoft\\Windows\\CurrentVersion\\Run'
        });

        regKey.get('WindowsAI', (err, item) => {
            if (err || !item) {
                callback(false);
            } else {
                callback(true);
            }
        });

    } catch (error) {
        // Fallback: Check for shortcut
        const shortcutPath = path.join(
            process.env.APPDATA,
            'Microsoft',
            'Windows',
            'Start Menu',
            'Programs',
            'Startup',
            'WindowsAI.lnk'
        );

        callback(fs.existsSync(shortcutPath));
    }
}

/**
 * Toggle startup on/off
 */
function toggleStartup(callback) {
    isInStartup((enabled) => {
        if (enabled) {
            removeFromStartup();
            callback(false);
        } else {
            addToStartup();
            callback(true);
        }
    });
}

/**
 * Auto-configure startup on first run
 * Should be called when app is first installed
 */
function configureStartupOnInstall() {
    const settingsPath = path.join(app.getPath('userData'), 'startup-configured.flag');

    if (!fs.existsSync(settingsPath)) {
        console.log('First run detected - configuring auto-startup');
        addToStartup();

        // Create flag file
        fs.writeFileSync(settingsPath, new Date().toISOString());
        return true;
    }

    return false;
}

module.exports = {
    addToStartup,
    removeFromStartup,
    isInStartup,
    toggleStartup,
    configureStartupOnInstall
};
