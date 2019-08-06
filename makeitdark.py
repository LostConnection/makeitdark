#!/usr/bin/env python

from sys import platform, argv
import os


def apply_sudo(sudo, command):
    return "sudo " + command if sudo else command


# Unpacks the Slack app and returns the ssb-interop.bundle.js file path
def unpack_app(sudo, packed_path):
    unpack_command = apply_sudo(sudo, "npx asar extract {0}/app.asar {0}/app.asar.unpacked".format(packed_path))
    os.system(unpack_command)
    return "{0}/app.asar.unpacked/dist/ssb-interop.bundle.js".format(packed_path)


# Removes the previously packed app and repacks it.
def pack_app(sudo, packed_path):
    remove_packed_command = apply_sudo(sudo, "rm -rf {0}/app.asar".format(packed_path))
    os.system(remove_packed_command)
    pack_command = apply_sudo(sudo, "npx asar pack {0}/app.asar.unpacked {0}/app.asar".format(packed_path))
    os.system(pack_command)
    return


# Markers for the injected css content
BEGIN_MARKER = "/* BEGIN makeitdark */"
END_MARKER = "/* END makeitdark */"

undo_mode = False

if len(argv) != 1:
    if argv[1] == "makeitlight":
        undo_mode = True
    else:
        print("run 'python ./makeitdark.py makeitlight' to undo the changes")
        exit()

injectable = BEGIN_MARKER + " \n\
   document.addEventListener(\"DOMContentLoaded\", function() {  \n\
   \n\
    /* Then get its webviews */  \n\
    let webviews = document.querySelectorAll(\".TeamView webview\");  \n\
   \n\
    /* Fetch CSS in parallel ahead of time from cdn host */  \n\
    const cssPath = 'https://raw.githubusercontent.com/LostConnection/makeitdark/master/darkreader.css';  \n\
    let cssPromise = fetch(cssPath).then(response => response.text());  \n\
   \n\
    /* Insert a style tag into the wrapper view */  \n\
    cssPromise.then(css => {  \n\
        let s = document.createElement('style');  \n\
        s.type = 'text/css';  \n\
        s.innerHTML = css;  \n\
        document.head.appendChild(s);  \n\
    });  \n\
   \n\
    /* Wait for each webview to load */  \n\
    webviews.forEach(webview => {  \n\
        webview.addEventListener('ipc-message', message => {  \n\
            if (message.channel == 'didFinishLoading')  \n\
            /* Finally add the CSS into the webview */  \n\
            cssPromise.then(css => {  \n\
                let script = `  \n\
                    let s = document.createElement('style');  \n\
                    s.type = 'text/css';  \n\
                    s.id = 'slack-custom-css';  \n\
                    s.innerHTML = \`${css}\`;  \n\
                    document.head.appendChild(s);  \n\
                `  \n\
                webview.executeJavaScript(script);  \n\
            })  \n\
        });  \n\
    });  \n\
}); \n " + END_MARKER

slack_packed_path = ""
require_sudo = True

if platform == "linux" or platform == "linux2":
    # linux
    print("Detected linux OS")
    slack_packed_path = "/usr/lib/slack/resources"
elif platform == "darwin":
    # OS X
    print("Detected OS X")
    slack_packed_path = "/Applications/Slack.app/Contents/Resources"
else:
    # Probably Windows
    require_sudo = False
    for root in os.environ['LOCALAPPDATA'], os.environ['PROGRAMFILES']:
        slack_root_path = os.path.join(root, "slack")
        if not os.path.exists(slack_root_path):  
            print("Slack not found at {0}".format(slack_root_path))
            continue
        slack_versions = sorted([slack_version for slack_version in os.listdir(slack_root_path) if
                                 slack_version.startswith("app-") and os.path.isdir(
                                     os.path.join(slack_root_path, slack_version))], reverse=True)
        if not slack_versions:
            continue

        most_recent = slack_versions[0]
        print("Searching for most recent slack update in {0}".format(slack_root_path))
        print("Found {0}".format(most_recent))
        slack_packed_path = os.path.join(slack_root_path, most_recent, "resources")
        if not os.path.exists(slack_packed_path):
            continue
        break
    else:
        raise EnvironmentError("Could not find slack installation")

# Unpack the Slack App
slack_theme_path = unpack_app(require_sudo, slack_packed_path)

if undo_mode:
    with open(slack_theme_path, "r+", encoding="utf8") as f:
        s = ""
        if BEGIN_MARKER not in f.read():
            print("Your slack theme is not dark yet")
            exit()
        else:
            f.seek(0, 0)
        for line in f:
            if BEGIN_MARKER not in line:
                s = s + line
            else:
                f.seek(0, 0)
                f.truncate()
                f.write(s)
                f.close()
                pack_app(require_sudo, slack_packed_path)
                print("Your slack theme has been updated, please restart slack")
                exit()
else:
    with open(slack_theme_path, "r+", encoding="utf8") as f:
        if BEGIN_MARKER in f.read():
            print("Your slack theme is already dark")
            exit()
        else:
            f.seek(0, 2)
            f.write("\n" + injectable)
            f.close()
            pack_app(require_sudo, slack_packed_path)
            print("Your slack theme has been updated, please restart slack")
            exit()
