#!/usr/bin/env python

from sys import platform, argv
import os

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
    const cssPath = 'https://raw.githubusercontent.com/jszklarz-haventec/makeitdark/master/darkreader.css';  \n\
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

slack_theme_path = ""

if platform == "linux" or platform == "linux2":
    # linux
    print("Detected linux OS")
    slack_theme_path = "/usr/lib/slack/resources/app.asar.unpacked/src/static/ssb-interop.js"
elif platform == "darwin":
    # OS X
    print("Detected OS X")
    slack_theme_path = "/Applications/Slack.app/Contents/Resources/app.asar.unpacked/src/static/ssb-interop.js"
else:
    # Probably Windows
    slack_root_path = os.path.join(os.environ['LOCALAPPDATA'], "slack")
    most_recent = sorted([slack_version for slack_version in os.listdir(slack_root_path) if slack_version.startswith("app-") and os.path.isdir(os.path.join(slack_root_path, slack_version))], reverse=True)[0]
    print("Searching for most recent slack update in {0}".format(slack_root_path))
    print("Found {0}".format(most_recent))
    slack_theme_path = os.path.join(slack_root_path, most_recent, "resources", "app.asar.unpacked", "src", "static", "ssb-interop.js")

if undo_mode:
    with open(slack_theme_path, "r+") as f:
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
                print("Your slack theme has been updated, please restart slack")
                exit()

else:
    with open(slack_theme_path, "r+") as f:
        if BEGIN_MARKER in f.read():
            print("Your slack theme is already dark")
            exit()
        else:
            f.seek(0, 2)
            f.write("\n" + injectable)
            f.close()
            print("Your slack theme has been updated, please restart slack")
            exit()
