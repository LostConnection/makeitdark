#!/usr/bin/env python

from sys import platform, argv
import os
if len(argv) != 1:
    if argv[1] == "makeitlight":
        undo_mode = True
    else:
        print("run 'python ./makeitdark.py makeitlight' to undo the changes")
        exit()
else:
    undo_mode = False

injectable = "/* BEGIN makeitdark */ \n\
   document.addEventListener(\"DOMContentLoaded\", function() {  \n\
   \n\
    /* Then get its webviews */  \n\
    let webviews = document.querySelectorAll(\".TeamView webview\");  \n\
   \n\
    /* Fetch CSS in parallel ahead of time from cdn host */  \n\
    const cssPath = 'https://raw.githubusercontent.com/ahayworth/makeitdark/master/slack-night-mode/css/raw/black.css';  \n\
    let cssPromise = fetch(cssPath).then(response => response.text());  \n\
   \n\
    let customCustomCSS = `  \n\
    :root {  \n\
        /* Modify these to change your theme colors: */  \n\
        --primary: #61AFEF;  \n\
        --text: #00FF00;  \n\
    }  \n\
    div.c-message.c-message--light.c-message--hover {  \n\
        color: #00FF00 !important;  \n\
    }  \n\
   \n\
    a.c-message__sender_link { color: #FFFFFF !important; }  \n\
   \n\
    span.c-message__body, span.c-message_attachment__media_trigger.c-message_attachment__media_trigger--caption,  \n\
    div.p-message_pane__foreword__description span {  \n\
        color: #00FF00 !important;  \n\
        font-family: \"Fira Code\", Arial, Helvetica, sans-serif;  \n\
        text-rendering: optimizeLegibility;  \n\
        font-size: 14px;  \n\
    }  \n\
   \n\
    div.c-virtual_list__scroll_container {  \n\
        background-color: #080808 !important;  \n\
    }  \n\
   \n\
    .p-message_pane .c-message_list:not(.c-virtual_list--scrollbar),  \n\
    .p-message_pane .c-message_list.c-virtual_list--scrollbar > .c-scrollbar__hider {  \n\
        z-index: 0;  \n\
    }  \n\
   \n\
   \n\
    div.c-message__content:hover {  \n\
        background-color: #080808 !important;  \n\
    }  \n\
   \n\
    div.c-message:hover {  \n\
        background-color: #080808 !important;  \n\
    }`  \n\
   \n\
    /* Insert a style tag into the wrapper view */  \n\
    cssPromise.then(css => {  \n\
        let s = document.createElement('style');  \n\
        s.type = 'text/css';  \n\
        s.innerHTML = css + customCustomCSS;  \n\
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
                    s.innerHTML = \`${css + customCustomCSS}\`;  \n\
                    document.head.appendChild(s);  \n\
                `  \n\
                webview.executeJavaScript(script);  \n\
            })  \n\
        });  \n\
    });  \n\
}); \n\
/* END makeitdark */ "

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
        if "/* BEGIN makeitdark */" not in f.read():
            print("Didn't make it dark yet")
            exit()
        else:
            f.seek(0,0)
        for line in f:
            if '/* BEGIN' not in line:
                s = s + line
            else:
                f.seek(0,0)
                f.truncate()
                f.write(s)
                print("lightened")
                exit()

else:
    with open(slack_theme_path, "r+") as f:
        if "/* BEGIN makeitdark */" in f.read():
            print("Already made it dark")
            exit()
        else:
            f.seek(0, 2)
            f.write("\n" + injectable)
            f.close()
            print("Your slack theme has been updated, please restart slack")
            exit()
