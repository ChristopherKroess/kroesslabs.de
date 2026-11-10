#!/usr/bin/env python3
"""Build kroesslabs.de.

Writes every page as plain HTML next to this repository's assets. GitHub Pages
serves the output as is; there is no build step on the server.

    python3 tools/build.py

Page copy lives in this file (APPS, HOME, PAGES). Legal texts live as HTML
fragments in src/legal/ and are wrapped in the site layout unchanged.
"""

from __future__ import annotations

import html
import json
import pathlib
import re

import intern

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
SITE = "https://kroesslabs.de"
EMAIL = "info.sidequests.app@gmail.com"
YEAR = 2026
ASSET_VERSION = "3"

# Version tag of the encrypted internal page (tools/intern.py); None if there is none.
INTERN_VERSION: str | None = None
INTERN_URL = "/intern/"

# --------------------------------------------------------------------------
# Icons (inline SVG, stroke style, 24x24)
# --------------------------------------------------------------------------

_I = {
    "arrow": '<path d="M5 12h14M13 6l6 6-6 6"/>',
    "shield": '<path d="M12 3l7 3v6c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6l7-3z"/><path d="M9 12l2 2 4-4"/>',
    "target": '<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="4"/><circle cx="12" cy="12" r=".6" fill="currentColor"/>',
    "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
    "heart": '<path d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10z"/>',
    "pulse": '<path d="M3 12h4l2-5 4 10 2-5h6"/>',
    "sparkles": '<path d="M12 3l1.8 4.7L18.5 9.5l-4.7 1.8L12 16l-1.8-4.7L5.5 9.5l4.7-1.8L12 3z"/><path d="M19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8L19 15z"/>',
    "bell": '<path d="M6 16V11a6 6 0 1 1 12 0v5l2 2H4l2-2z"/><path d="M10 20a2 2 0 0 0 4 0"/>',
    "archive": '<rect x="3" y="4" width="18" height="5" rx="1.5"/><path d="M5 9v9a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V9M10 13h4"/>',
    "globe": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.5 2.6 3.8 5.6 3.8 9s-1.3 6.4-3.8 9c-2.5-2.6-3.8-5.6-3.8-9S9.5 5.6 12 3z"/>',
    "layers": '<path d="M12 3l9 5-9 5-9-5 9-5z"/><path d="M3 13l9 5 9-5"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "users": '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20a6.5 6.5 0 0 1 13 0"/><path d="M16 4.5a3.5 3.5 0 0 1 0 7M18 14.5a6.5 6.5 0 0 1 3.5 5.5"/>',
    "user": '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
    "lock": '<rect x="4.5" y="10.5" width="15" height="10" rx="2.5"/><path d="M8 10.5V8a4 4 0 0 1 8 0v2.5"/>',
    "refresh": '<path d="M20 11a8 8 0 0 0-14.7-4.4L3 9"/><path d="M3 4v5h5M4 13a8 8 0 0 0 14.7 4.4L21 15"/><path d="M21 20v-5h-5"/>',
    "server": '<rect x="3.5" y="4" width="17" height="7" rx="2"/><rect x="3.5" y="13" width="17" height="7" rx="2"/><path d="M7.5 7.5h.01M7.5 16.5h.01"/>',
    "cloud": '<path d="M7 18a4.5 4.5 0 0 1-.5-9 6 6 0 0 1 11.5 1.5A3.75 3.75 0 0 1 17.5 18H7z"/>',
    "check": '<circle cx="12" cy="12" r="9"/><path d="M8 12.5l2.5 2.5L16 9.5"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/>',
    "mail": '<rect x="3" y="5" width="18" height="14" rx="2.5"/><path d="M3.5 6.5l8.5 6 8.5-6"/>',
    "pin": '<path d="M12 21s-7-6.2-7-11.5a7 7 0 0 1 14 0C19 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/>',
    "eye-off": '<path d="M3 3l18 18"/><path d="M10.6 5.1A10.4 10.4 0 0 1 12 5c6 0 9.5 7 9.5 7a17 17 0 0 1-3.2 4.1M6.6 6.6A16.6 16.6 0 0 0 2.5 12S6 19 12 19a9.8 9.8 0 0 0 4.4-1"/><path d="M9.9 9.9a3 3 0 0 0 4.2 4.2"/>',
    "calendar": '<rect x="3.5" y="5" width="17" height="15.5" rx="2.5"/><path d="M3.5 10h17M8 3v4M16 3v4"/>',
    "book": '<path d="M5 4.5A1.5 1.5 0 0 1 6.5 3H19v15H6.5A1.5 1.5 0 0 0 5 19.5v-15z"/><path d="M5 19.5A1.5 1.5 0 0 0 6.5 21H19"/>',
    "smile": '<circle cx="12" cy="12" r="9"/><path d="M8.5 14.5a4.5 4.5 0 0 0 7 0M9 9.5h.01M15 9.5h.01"/>',
    "flame": '<path d="M12 21c-3.9 0-7-2.7-7-6.5 0-3.4 2.7-5.2 3.8-8.5 2.2 1.4 3.2 3.3 3.2 5 1-1 1.6-2.3 1.7-3.7C16.4 9.4 19 12 19 14.5 19 18.3 15.9 21 12 21z"/>',
    "hand": '<path d="M7 11V5.5a1.5 1.5 0 0 1 3 0V10M10 9.5v-6a1.5 1.5 0 0 1 3 0v6M13 9.5V5a1.5 1.5 0 0 1 3 0v6.5M16 8.5a1.5 1.5 0 0 1 3 0V14a7 7 0 0 1-7 7h-.5a6.5 6.5 0 0 1-5.4-2.9L3.4 14a1.5 1.5 0 0 1 2.4-1.8L7 13.5"/>',
    "leaf": '<path d="M5 19c0-8 5.5-14 15-14 0 9.5-6 15-14 15"/><path d="M5 19l7-7"/>',
}


def icon(name: str) -> str:
    return (
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
        'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + _I[name] + "</svg>"
    )


# --------------------------------------------------------------------------
# Content
# --------------------------------------------------------------------------

UI = {
    "en": {
        "nav_apps": "Apps", "nav_studio": "Studio", "nav_contact": "Contact",
        "lang_label": "DE", "lang_name": "Deutsch", "lang_title": "Diese Seite auf Deutsch",
        "skip": "Skip to content", "home": "Kroess Labs home",
        "foot_tag": "An independent app studio from Freiburg, Germany. Small apps for a brighter everyday.",
        "foot_apps": "Apps", "foot_studio": "Studio", "foot_legal": "Legal",
        "about": "About the studio", "contact": "Contact", "legal": "Legal notice", "privacy": "Privacy",
        "q_privacy": "Quevia privacy policy", "intern": "Internal",
        "fine_right": "No cookies. No tracking. Nothing loaded from third parties.",
        "learn": "Learn more", "status_test": "In testing on Google Play", "status_dev": "In development",
    },
    "de": {
        "nav_apps": "Apps", "nav_studio": "Studio", "nav_contact": "Kontakt",
        "lang_label": "EN", "lang_name": "English", "lang_title": "This page in English",
        "skip": "Zum Inhalt springen", "home": "Kroess Labs Startseite",
        "foot_tag": "Ein unabhängiges App-Studio aus Freiburg. Kleine Apps für einen helleren Alltag.",
        "foot_apps": "Apps", "foot_studio": "Studio", "foot_legal": "Rechtliches",
        "about": "Über das Studio", "contact": "Kontakt", "legal": "Impressum", "privacy": "Datenschutz",
        "q_privacy": "Datenschutzerklärung Quevia", "intern": "Intern",
        "fine_right": "Keine Cookies. Kein Tracking. Nichts von Drittanbietern.",
        "learn": "Mehr erfahren", "status_test": "Im Test bei Google Play", "status_dev": "In Entwicklung",
    },
}

# Per-language URL of each logical page.
URLS = {
    "home": {"en": "/", "de": "/de/"},
    "quevia": {"en": "/quevia/", "de": "/de/quevia/"},
    "spark": {"en": "/spark/", "de": "/de/spark/"},
    "berryvault": {"en": "/berryvault/", "de": "/de/berryvault/"},
    "legal": {"en": "/legal-notice/", "de": "/impressum/"},
    "privacy": {"en": "/privacy/", "de": "/datenschutz/"},
    "quevia_privacy": {"en": "/quevia/privacy/", "de": "/quevia/datenschutz/"},
}

APPS = [
    {
        "key": "quevia", "name": "Quevia", "status": "test",
        "icon": "/assets/img/quevia-icon.webp", "art": "quevia", "flip": True,
        "platforms": {"en": "Android · iOS", "de": "Android · iOS"},
        "card": {
            "en": "Every day, a little adventure. Pick one of three small real-life quests, go do it, and level up.",
            "de": "Jeden Tag ein kleines Abenteuer. Wähl eine von drei Quests im echten Leben, zieh sie durch und steig im Level auf.",
        },
    },
    {
        "key": "spark", "name": "Spark", "status": "dev",
        "icon": "/assets/img/spark-icon.svg", "art": "spark", "flip": False,
        "platforms": {"en": "Android", "de": "Android"},
        "card": {
            "en": "Three small gestures a day and one date a week, to keep your relationship warm.",
            "de": "Drei kleine Gesten am Tag und ein Date pro Woche, damit eure Beziehung warm bleibt.",
        },
    },
    {
        "key": "berryvault", "name": "BerryVault", "status": "dev",
        "icon": "/assets/img/berryvault-icon.webp", "art": "berryvault", "flip": False,
        "platforms": {"en": "iPhone", "de": "iPhone"},
        "card": {
            "en": "Your Apple Health data, continuously exported to your own server or your OneDrive.",
            "de": "Deine Apple-Health-Daten, laufend exportiert auf deinen eigenen Server oder in dein OneDrive.",
        },
    },
]

HOME = {
    "en": {
        "title": "Kroess Labs · Small apps for a brighter everyday",
        "desc": "Kroess Labs is an independent app studio from Freiburg, Germany, making calm, private apps: Quevia, Spark and BerryVault.",
        "eyebrow": "Independent app studio · Freiburg",
        "h1": 'Small apps for a <span class="glow-text">brighter</span> everyday.',
        "lead": "Kroess Labs makes calm, private apps that do one thing well, so you spend less time on your phone and more time on your life.",
        "cta1": "Explore the apps", "cta2": "Get in touch",
        "apps_eyebrow": "The apps",
        "apps_h2": "Three apps, one idea: real life first.",
        "apps_p": "Each app is small on purpose. No feeds, no noise, no account you don’t need.",
        "soon_h": "More on the way",
        "soon_p": "Two more apps are taking shape in the lab. Their names are still a secret, even to us.",
        "how_eyebrow": "How we build",
        "how_h2": "Made to be put down.",
        "how_p": "Good apps fit into your day and then get out of the way. These are the rules we build by.",
        "principles": [
            ("shield", "Private by design", "No tracking and no selling of data. What you do in our apps stays on your device, or goes only where you send it."),
            ("target", "Small and focused", "Each app does one job and does it well. No endless feeds, no features for the sake of features."),
            ("sun", "Real life first", "Our apps ask for a minute, not an evening. The best part happens away from the screen."),
            ("sparkles", "Crafted with care", "Designed and built in Freiburg, with attention to every detail, from the first tap to the last reminder."),
        ],
        "studio_eyebrow": "The studio",
        "studio_h2": "A small studio at the edge of the Black Forest.",
        "studio_p1": "Kroess Labs is an independent app studio based in Freiburg im Breisgau, Germany. We design, build and look after every app ourselves, for Android and iPhone.",
        "studio_p2": "We make the kind of apps we want on our own phones: useful, beautiful and respectful of your time and your data.",
        "facts": [
            ("pin", "Freiburg im Breisgau", "Made in Germany, at the edge of the Black Forest."),
            ("user", "Independent", "We answer to the people who use our apps, nobody else."),
            ("eye-off", "A website without tracking", "No cookies, no analytics, nothing loaded from third parties."),
        ],
        "contact_eyebrow": "Contact",
        "contact_h2": "Questions, feedback or an idea?",
        "contact_p": "We read every message. Write to us and we’ll get back to you.",
    },
    "de": {
        "title": "Kroess Labs · Kleine Apps für einen helleren Alltag",
        "desc": "Kroess Labs ist ein unabhängiges App-Studio aus Freiburg. Wir machen ruhige, private Apps: Quevia, Spark und BerryVault.",
        "eyebrow": "Unabhängiges App-Studio · Freiburg",
        "h1": 'Kleine Apps für einen <span class="glow-text">helleren</span> Alltag.',
        "lead": "Kroess Labs macht ruhige, private Apps, die eine Sache richtig gut können. Damit du weniger Zeit am Handy verbringst und mehr Zeit in deinem Leben.",
        "cta1": "Zu den Apps", "cta2": "Kontakt aufnehmen",
        "apps_eyebrow": "Die Apps",
        "apps_h2": "Drei Apps, eine Idee: das echte Leben zuerst.",
        "apps_p": "Jede App ist mit Absicht klein. Kein Feed, kein Lärm, kein Konto, das du nicht brauchst.",
        "soon_h": "Es kommt noch mehr",
        "soon_p": "Zwei weitere Apps nehmen gerade im Labor Gestalt an. Ihre Namen sind noch geheim, sogar für uns.",
        "how_eyebrow": "Wie wir bauen",
        "how_h2": "Gemacht, um sie wieder wegzulegen.",
        "how_p": "Gute Apps passen in deinen Tag und gehen dir dann aus dem Weg. Nach diesen Regeln bauen wir.",
        "principles": [
            ("shield", "Privat von Anfang an", "Kein Tracking und kein Verkauf von Daten. Was du in unseren Apps tust, bleibt auf deinem Gerät oder geht nur dorthin, wohin du es schickst."),
            ("target", "Klein und fokussiert", "Jede App macht eine Sache und die richtig. Keine endlosen Feeds, keine Funktionen um der Funktionen willen."),
            ("sun", "Das echte Leben zuerst", "Unsere Apps wollen eine Minute, nicht deinen Abend. Das Beste passiert abseits des Bildschirms."),
            ("sparkles", "Mit Sorgfalt gemacht", "Gestaltet und entwickelt in Freiburg, mit Liebe zum Detail, vom ersten Tippen bis zur letzten Erinnerung."),
        ],
        "studio_eyebrow": "Das Studio",
        "studio_h2": "Ein kleines Studio am Rand des Schwarzwalds.",
        "studio_p1": "Kroess Labs ist ein unabhängiges App-Studio in Freiburg im Breisgau. Wir gestalten, entwickeln und pflegen jede App selbst, für Android und iPhone.",
        "studio_p2": "Wir machen die Apps, die wir selbst auf dem Handy haben wollen: nützlich, schön und respektvoll mit deiner Zeit und deinen Daten.",
        "facts": [
            ("pin", "Freiburg im Breisgau", "Gemacht in Deutschland, am Rand des Schwarzwalds."),
            ("user", "Unabhängig", "Wir sind den Menschen verpflichtet, die unsere Apps nutzen, sonst niemandem."),
            ("eye-off", "Eine Website ohne Tracking", "Keine Cookies, keine Analyse, nichts von Drittanbietern."),
        ],
        "contact_eyebrow": "Kontakt",
        "contact_h2": "Fragen, Feedback oder eine Idee?",
        "contact_p": "Wir lesen jede Nachricht. Schreib uns, wir melden uns.",
    },
}

APP_PAGES = {
    "quevia": {
        "en": {
            "title": "Quevia · Every day, a little adventure",
            "desc": "Quevia gives you one small real-life adventure a day: pick one of three quests, go do it, level up. No account, no ads, no tracking.",
            "h1": "Every day, a little adventure.",
            "lead": "Your evening deserves better than another hour of scrolling. Quevia gives you one small, real-life adventure a day.",
            "cta1": "How it works", "cta2": "Privacy policy",
            "note": "Quevia is in a closed test on Google Play right now. The public release on Google Play and the App Store follows soon.",
            "how_eyebrow": "How it works", "how_h2": "Pick one. Go do it. Level up.",
            "how_p": "Every morning Quevia offers three Daily Quests. Choose one, do it, and check it off in the evening. That’s it.",
            "steps": [
                ("Every morning: three Daily Quests", "Pick one, and it’s yours for the day."),
                ("Every week: three Weekly Quests", "Bigger ones, with the whole week to do them."),
                ("Done? Check it off", "Earn XP, level up and keep your daily streak going. Tapped the wrong one? Undo it right away."),
            ],
            "shots_eyebrow": "A look inside", "shots_h2": "Simple on the surface. Thoughtful underneath.",
            "feat_eyebrow": "Features", "feat_h2": "Everything you need, nothing you don’t.",
            "features": [
                ("layers", "133 quests in five categories", "Social, Body, Creativity, Mind and Adventure. Quests you’ve completed don’t come back, so there’s always something new."),
                ("flame", "Five minutes or a little courage", "Smile at three strangers today, or set up a full sit-down dinner somewhere outdoors, like a forest or a rooftop."),
                ("bell", "Reminders that know when to stay quiet", "One nudge in the morning to pick, one in the evening to confirm. Skipped when there’s nothing left to do."),
                ("lock", "Private by design", "No account. No ads. No tracking. Quevia doesn’t even ask for internet access: everything stays on your phone."),
                ("archive", "Your adventure archive", "A searchable archive of everything you’ve done, with your XP, level and streak."),
                ("globe", "15 languages, light and dark", "Switch the language right in the app, and pick light or dark mode."),
            ],
            "privacy_eyebrow": "Privacy", "privacy_h2": "Your adventures stay on your phone.",
            "privacy_p": "Quevia stores your quests and progress only on your device. The Android app doesn’t even request internet access, and the iOS app makes no network connections.",
        },
        "de": {
            "title": "Quevia · Jeden Tag ein kleines Abenteuer",
            "desc": "Quevia gibt dir jeden Tag ein kleines Abenteuer im echten Leben: eine von drei Quests wählen, durchziehen, aufsteigen. Kein Konto, keine Werbung, kein Tracking.",
            "h1": "Jeden Tag ein kleines Abenteuer.",
            "lead": "Dein Abend kann mehr als noch eine Stunde Scrollen. Quevia gibt dir jeden Tag ein kleines Abenteuer im echten Leben.",
            "cta1": "So funktioniert’s", "cta2": "Datenschutzerklärung",
            "note": "Quevia ist gerade im geschlossenen Test bei Google Play. Die öffentliche Version für Google Play und den App Store folgt bald.",
            "how_eyebrow": "So funktioniert’s", "how_h2": "Wählen. Machen. Aufsteigen.",
            "how_p": "Jeden Morgen warten drei Tages-Quests auf dich. Such dir eine aus, zieh sie durch und hak sie abends ab. Mehr nicht.",
            "steps": [
                ("Jeden Morgen: drei Tages-Quests", "Du wählst eine, und die gehört dir für heute."),
                ("Jede Woche: drei Wochen-Quests", "Größere Sachen, für die du die ganze Woche Zeit hast."),
                ("Geschafft? Abhaken", "XP sammeln, im Level aufsteigen und deine Serie am Laufen halten. Daneben getippt? Direkt rückgängig machen."),
            ],
            "shots_eyebrow": "Ein Blick hinein", "shots_h2": "Einfach an der Oberfläche. Durchdacht im Detail.",
            "feat_eyebrow": "Funktionen", "feat_h2": "Alles, was du brauchst. Nichts, was du nicht brauchst.",
            "features": [
                ("layers", "133 Quests in fünf Kategorien", "Sozial, Körper, Kreativ, Kopf und Abenteuer. Erledigte Quests kommen nicht wieder, es gibt also immer etwas Neues."),
                ("flame", "Fünf Minuten oder ein bisschen Mut", "Lächel heute drei fremde Menschen an, oder deck irgendwo draußen einen richtigen Tisch fürs Dinner, im Wald oder auf einem Dach."),
                ("bell", "Erinnerungen, die wissen, wann sie still sein sollen", "Morgens ein Stupser zum Auswählen, abends einer zum Abhaken. Wenn nichts mehr zu tun ist, bleibt die Erinnerung aus."),
                ("lock", "Privat von Anfang an", "Kein Konto. Keine Werbung. Kein Tracking. Quevia fragt nicht einmal nach Internetzugriff: Alles bleibt auf deinem Handy."),
                ("archive", "Dein Abenteuer-Archiv", "Ein durchsuchbares Archiv mit allem, was du schon geschafft hast, samt XP, Level und Serie."),
                ("globe", "15 Sprachen, hell und dunkel", "Die Sprache stellst du direkt in der App um, dazu heller oder dunkler Modus."),
            ],
            "privacy_eyebrow": "Datenschutz", "privacy_h2": "Deine Abenteuer bleiben auf deinem Handy.",
            "privacy_p": "Quevia speichert deine Quests und deinen Fortschritt nur auf deinem Gerät. Die Android-App fragt nicht einmal nach Internetzugriff, und die iOS-App baut keine Netzwerkverbindungen auf.",
        },
    },
    "spark": {
        "en": {
            "title": "Spark · Keep the spark alive",
            "desc": "Spark suggests three small gestures every day and three date ideas every week, to keep your relationship warm. Private, no account. In development.",
            "h1": "Keep the spark alive, one small gesture at a time.",
            "lead": "Every day Spark suggests three small gestures, and every week three date ideas. Pick one, do it, and feel your relationship grow warmer.",
            "cta1": "How it works", "cta2": None,
            "note": "Spark is in development for Android. Its name may still change before launch.",
            "how_eyebrow": "How it works", "how_h2": "Small gestures, every day.",
            "how_p": "Love lives in the little things. Spark makes them easy to remember and fun to do.",
            "steps": [
                ("Every day: three small gestures", "From three different kinds of care. Most take under 15 minutes and cost nothing."),
                ("Every week: three date ideas", "From cozy to adventurous. Pick one and enjoy it together before Sunday."),
                ("Keep your memories", "Save the dates you’ve had in a memory book, with a photo and a note if you like."),
            ],
            "feat_eyebrow": "What makes it different", "feat_h2": "Deeds, not questionnaires.",
            "features": [
                ("heart", "Variety instead of labels", "Kind words, quality time, helpful acts, small gifts and closeness: a balanced mix every day, no personality test."),
                ("user", "Works on your own", "Your partner doesn’t need the app. One of you is enough to make a difference."),
                ("lock", "Private, no account", "Your gestures and memories stay on your phone."),
                ("flame", "A gentle daily streak", "A reason to check in every day, without levels, points or scores."),
                ("calendar", "Five kinds of dates", "Active, relaxing, emotional, creative and culinary, so every week feels different."),
                ("book", "Hand-picked ideas", "Every gesture and every date is chosen and checked by hand before it goes into the app."),
            ],
            "privacy_eyebrow": "Privacy", "privacy_h2": "What happens between you two stays between you two.",
            "privacy_p": "Spark is being built to work without an account and to keep everything on your device. A full privacy policy will be published here before launch.",
        },
        "de": {
            "title": "Spark · Damit der Funke bleibt",
            "desc": "Spark schlägt jeden Tag drei kleine Gesten und jede Woche drei Date-Ideen vor, damit eure Beziehung warm bleibt. Privat, ohne Konto. In Entwicklung.",
            "h1": "Damit der Funke bleibt, eine kleine Geste nach der anderen.",
            "lead": "Jeden Tag schlägt Spark drei kleine Gesten vor, jede Woche drei Date-Ideen. Such dir eine aus, mach sie, und spür, wie eure Beziehung wärmer wird.",
            "cta1": "So funktioniert’s", "cta2": None,
            "note": "Spark ist für Android in Entwicklung. Der Name kann sich bis zum Start noch ändern.",
            "how_eyebrow": "So funktioniert’s", "how_h2": "Kleine Gesten, jeden Tag.",
            "how_p": "Liebe steckt in den kleinen Dingen. Spark sorgt dafür, dass du sie nicht vergisst und dass sie Spaß machen.",
            "steps": [
                ("Jeden Tag: drei kleine Gesten", "Aus drei verschiedenen Arten von Zuwendung. Meist unter 15 Minuten und meist kostenlos."),
                ("Jede Woche: drei Date-Ideen", "Von gemütlich bis abenteuerlich. Eine aussuchen und bis Sonntag zusammen erleben."),
                ("Erinnerungen behalten", "Eure Dates landen in einem Erinnerungsbuch, auf Wunsch mit Foto und Notiz."),
            ],
            "feat_eyebrow": "Was Spark anders macht", "feat_h2": "Taten statt Fragebögen.",
            "features": [
                ("heart", "Abwechslung statt Schubladen", "Liebe Worte, gemeinsame Zeit, kleine Hilfen, Geschenke und Nähe: jeden Tag eine ausgewogene Mischung, ohne Persönlichkeitstest."),
                ("user", "Funktioniert auch allein", "Dein Partner oder deine Partnerin braucht die App nicht. Einer von euch reicht, um etwas zu bewegen."),
                ("lock", "Privat, ohne Konto", "Deine Gesten und Erinnerungen bleiben auf deinem Handy."),
                ("flame", "Eine sanfte Serie", "Ein Grund, jeden Tag reinzuschauen, ohne Level, Punkte oder Ranglisten."),
                ("calendar", "Fünf Arten von Dates", "Action, Entspannung, Emotional, Kreativ und Kulinarisch, damit sich jede Woche anders anfühlt."),
                ("book", "Handverlesene Ideen", "Jede Geste und jedes Date wird von Hand ausgewählt und geprüft, bevor es in die App kommt."),
            ],
            "privacy_eyebrow": "Datenschutz", "privacy_h2": "Was zwischen euch passiert, bleibt zwischen euch.",
            "privacy_p": "Spark wird so gebaut, dass es ohne Konto funktioniert und alles auf deinem Gerät bleibt. Die vollständige Datenschutzerklärung erscheint hier vor dem Start.",
        },
    },
    "berryvault": {
        "en": {
            "title": "BerryVault · Your health data, in your own hands",
            "desc": "BerryVault continuously exports your Apple Health data to your own server or your OneDrive. No middleman, no lock-in. In development for iPhone.",
            "h1": "Your health data, in your own hands.",
            "lead": "BerryVault continuously exports your Apple Health data to a destination you choose: your own server, like a Raspberry Pi at home, or your OneDrive. No middleman, no lock-in.",
            "cta1": "How it works", "cta2": None,
            "note": "BerryVault is in development for iPhone and not yet available on the App Store.",
            "how_eyebrow": "How it works", "how_h2": "Set it up once. Then forget about it.",
            "how_p": "BerryVault runs quietly in the background and keeps your own copy of your health data up to date.",
            "steps": [
                ("Allow access", "Choose which Health data BerryVault may read. It never writes to Apple Health."),
                ("Pick a destination", "Your own server on your home network, or a private app folder in your OneDrive."),
                ("Let it sync", "BerryVault sends new data when you open the app, unlock your iPhone or Health reports new samples, and retries on its own if a transfer fails."),
            ],
            "feat_eyebrow": "Features", "feat_h2": "Complete, careful and yours.",
            "features": [
                ("pulse", "Everything Apple Health offers", "Sleep and sleep stages, heart rate and HRV, workouts and routes, ECGs, nutrition, mood and much more: over 190 data types."),
                ("refresh", "Only what’s new", "Each sync sends just what was added, changed or deleted since last time. Deletions arrive exactly, without duplicates."),
                ("shield", "Built for reliability", "Data is only removed from the queue once every destination has confirmed it. Unfinished uploads complete in the background."),
                ("server", "Your server or OneDrive", "Send your data to your own server at home, or to a folder in OneDrive that only BerryVault can reach."),
                ("info", "Clear when something’s wrong", "If a login expires or your server can’t be reached, BerryVault tells you exactly what to do."),
                ("eye-off", "Read-only and private", "BerryVault only reads your data and sends it nowhere but to the destinations you set up."),
            ],
            "privacy_eyebrow": "Privacy", "privacy_h2": "No cloud in between.",
            "privacy_p": "Your health data goes straight from your iPhone to your own destination. There is no BerryVault server and no account. A full privacy policy will be published here before launch.",
        },
        "de": {
            "title": "BerryVault · Deine Gesundheitsdaten in deiner Hand",
            "desc": "BerryVault exportiert deine Apple-Health-Daten laufend auf deinen eigenen Server oder in dein OneDrive. Ohne Zwischenstation, ohne Lock-in. In Entwicklung fürs iPhone.",
            "h1": "Deine Gesundheitsdaten in deiner Hand.",
            "lead": "BerryVault exportiert deine Apple-Health-Daten laufend an ein Ziel deiner Wahl: deinen eigenen Server, zum Beispiel einen Raspberry Pi zu Hause, oder dein OneDrive. Ohne Zwischenstation, ohne Lock-in.",
            "cta1": "So funktioniert’s", "cta2": None,
            "note": "BerryVault ist fürs iPhone in Entwicklung und noch nicht im App Store erhältlich.",
            "how_eyebrow": "So funktioniert’s", "how_h2": "Einmal einrichten. Dann vergessen.",
            "how_p": "BerryVault läuft leise im Hintergrund und hält deine eigene Kopie deiner Gesundheitsdaten aktuell.",
            "steps": [
                ("Zugriff erlauben", "Du wählst, welche Health-Daten BerryVault lesen darf. In Health schreibt die App nie."),
                ("Ziel wählen", "Dein eigener Server im Heimnetz oder ein privater App-Ordner in deinem OneDrive."),
                ("Synchronisieren lassen", "BerryVault schickt neue Daten, wenn du die App öffnest, das iPhone entsperrst oder Health Neues meldet, und versucht es bei Fehlern von selbst erneut."),
            ],
            "feat_eyebrow": "Funktionen", "feat_h2": "Vollständig, sorgfältig und deins.",
            "features": [
                ("pulse", "Alles, was Apple Health bietet", "Schlaf und Schlafphasen, Puls und HRV, Workouts und Routen, EKGs, Ernährung, Gemütszustand und vieles mehr: über 190 Datentypen."),
                ("refresh", "Nur, was neu ist", "Jeder Sync schickt nur, was seit dem letzten Mal hinzukam, sich geändert hat oder gelöscht wurde. Löschungen kommen exakt an, ohne Duplikate."),
                ("shield", "Auf Zuverlässigkeit gebaut", "Daten verlassen die Warteschlange erst, wenn jedes Ziel sie bestätigt hat. Angefangene Uploads laufen im Hintergrund zu Ende."),
                ("server", "Dein Server oder OneDrive", "Schick deine Daten an deinen eigenen Server zu Hause oder in einen OneDrive-Ordner, auf den nur BerryVault zugreift."),
                ("info", "Klar, wenn etwas hakt", "Wenn eine Anmeldung abläuft oder dein Server nicht erreichbar ist, sagt dir BerryVault genau, was zu tun ist."),
                ("eye-off", "Nur lesend und privat", "BerryVault liest deine Daten nur und schickt sie nirgendwohin außer an die Ziele, die du einrichtest."),
            ],
            "privacy_eyebrow": "Datenschutz", "privacy_h2": "Keine Cloud dazwischen.",
            "privacy_p": "Deine Gesundheitsdaten gehen direkt vom iPhone an dein eigenes Ziel. Es gibt keinen BerryVault-Server und kein Konto. Die vollständige Datenschutzerklärung erscheint hier vor dem Start.",
        },
    },
}

LEGAL_PAGES = [
    # key, lang, fragment, title, description
    ("legal", "en", "legal-notice.html", "Legal notice · Kroess Labs", "Legal notice (Impressum) for kroesslabs.de and the apps by Kroess Labs."),
    ("legal", "de", "impressum.html", "Impressum · Kroess Labs", "Impressum für kroesslabs.de und die Apps von Kroess Labs."),
    ("privacy", "en", "privacy.html", "Privacy policy for this website · Kroess Labs", "How kroesslabs.de handles your data: no cookies, no analytics, nothing loaded from third parties."),
    ("privacy", "de", "datenschutz.html", "Datenschutzerklärung für diese Website · Kroess Labs", "Wie kroesslabs.de mit deinen Daten umgeht: keine Cookies, keine Analyse, nichts von Drittanbietern."),
    ("quevia_privacy", "en", "quevia-privacy.html", "Quevia privacy policy · Kroess Labs", "Privacy policy for the Quevia app for Android and iOS."),
    ("quevia_privacy", "de", "quevia-datenschutz.html", "Datenschutzerklärung Quevia · Kroess Labs", "Datenschutzerklärung für die App Quevia für Android und iOS."),
]

# --------------------------------------------------------------------------
# Layout
# --------------------------------------------------------------------------


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def head(lang: str, key: str, title: str, desc: str, og_image: str = "/assets/img/og.jpg", preload: str | None = None) -> str:
    url = SITE + URLS[key][lang]
    other = "de" if lang == "en" else "en"
    alt = SITE + URLS[key][other]
    pre = f'\n<link rel="preload" as="image" href="{preload}" fetchpriority="high">' if preload else ""
    ld = ""
    if key == "home":
        ld = "\n<script type=\"application/ld+json\">" + json.dumps({
            "@context": "https://schema.org", "@type": "Organization", "name": "Kroess Labs",
            "url": SITE + "/", "logo": SITE + "/assets/img/icon-512.png", "email": EMAIL,
            "address": {"@type": "PostalAddress", "addressLocality": "Freiburg im Breisgau", "addressCountry": "DE"},
        }, ensure_ascii=False) + "</script>"
    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="theme-color" content="#070a12">
<meta name="color-scheme" content="dark">
<link rel="canonical" href="{url}">
<link rel="alternate" hreflang="{lang}" href="{url}">
<link rel="alternate" hreflang="{other}" href="{alt}">
<link rel="alternate" hreflang="x-default" href="{SITE + URLS[key]['en']}">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="preload" href="/assets/fonts/jakarta-latin.woff2" as="font" type="font/woff2" crossorigin>{pre}
<link rel="stylesheet" href="/assets/css/site.css?v={ASSET_VERSION}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Kroess Labs">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}{og_image}">
<meta property="og:locale" content="{'de_DE' if lang == 'de' else 'en_US'}">
<meta name="twitter:card" content="summary_large_image">{ld}
<script defer src="/assets/js/site.js?v={ASSET_VERSION}"></script>
</head>
"""


def header(lang: str, key: str) -> str:
    t = UI[lang]
    home = URLS["home"][lang]
    other = "de" if lang == "en" else "en"
    on_home = key == "home"
    apps = "#apps" if on_home else home + "#apps"
    studio = "#studio" if on_home else home + "#studio"
    contact = "#contact" if on_home else home + "#contact"
    return f"""<body>
<a class="skip" href="#main">{t['skip']}</a>
<header class="site-header">
  <div class="wrap">
    <a class="brand" href="{home}" aria-label="{t['home']}"><img src="/assets/img/logo.svg" alt="" width="30" height="30"><span><b>Kroess</b> <i>Labs</i></span></a>
    <nav class="nav" aria-label="Main">
      <a href="{apps}">{t['nav_apps']}</a>
      <a class="hide-sm" href="{studio}">{t['nav_studio']}</a>
      <a class="hide-sm" href="{contact}">{t['nav_contact']}</a>
      <a class="lang" href="{URLS[key][other]}" hreflang="{other}" lang="{other}" title="{t['lang_title']}">{t['lang_label']}</a>
    </nav>
  </div>
</header>
"""


def footer(lang: str, key: str) -> str:
    t = UI[lang]
    other = "de" if lang == "en" else "en"
    home = URLS["home"][lang]
    apps = "".join(f'<li><a href="{URLS[a["key"]][lang]}">{a["name"]}</a></li>' for a in APPS)
    lock = '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" style="vertical-align:-1px;margin-right:6px"><rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/></svg>'
    intern_link = f'\n        <li><a href="{INTERN_URL}" rel="nofollow">{lock}{t["intern"]}</a></li>' if INTERN_VERSION else ""
    return f"""<footer class="site-footer">
  <div class="wrap">
    <div class="foot">
      <div>
        <a class="brand" href="{home}"><img src="/assets/img/logo.svg" alt="" width="30" height="30"><span><b>Kroess</b> <i>Labs</i></span></a>
        <p>{t['foot_tag']}</p>
      </div>
      <div><h4>{t['foot_apps']}</h4><ul>{apps}</ul></div>
      <div><h4>{t['foot_studio']}</h4><ul>
        <li><a href="{home}#studio">{t['about']}</a></li>
        <li><a href="mailto:{EMAIL}">{t['contact']}</a></li>
        <li><a href="{URLS[key][other]}" hreflang="{other}" lang="{other}">{t['lang_name']}</a></li>{intern_link}
      </ul></div>
      <div><h4>{t['foot_legal']}</h4><ul>
        <li><a href="{URLS['legal'][lang]}">{t['legal']}</a></li>
        <li><a href="{URLS['privacy'][lang]}">{t['privacy']}</a></li>
        <li><a href="{URLS['quevia_privacy'][lang]}">{t['q_privacy']}</a></li>
      </ul></div>
    </div>
    <div class="fine"><span>© {YEAR} Kroess Labs · Freiburg im Breisgau</span><span>{t['fine_right']}</span></div>
  </div>
</footer>
</body>
</html>
"""


def page(lang: str, key: str, title: str, desc: str, main: str, preload: str | None = None) -> str:
    return head(lang, key, title, desc, preload=preload) + header(lang, key) + f'<main id="main">\n{main}\n</main>\n' + footer(lang, key)


def chip(status: str, lang: str) -> str:
    label = UI[lang]["status_test"] if status == "test" else UI[lang]["status_dev"]
    return f'<span class="chip {status}"><span class="dot"></span>{label}</span>'


# --------------------------------------------------------------------------
# Pages
# --------------------------------------------------------------------------


def home_page(lang: str) -> str:
    c = HOME[lang]
    t = UI[lang]
    cards = []
    for a in APPS:
        cards.append(f"""<a class="app-card reveal t-{a['key']}" href="{URLS[a['key']][lang]}">
        <div class="art"><img src="/assets/img/{a['art']}-800.webp" alt="" width="800" height="533" loading="lazy" decoding="async"></div>
        <div class="body">
          <img class="icon" src="{a['icon']}" alt="" width="64" height="64">
          <h3>{a['name']}</h3>
          <div class="chips">{chip(a['status'], lang)}<span class="chip">{a['platforms'][lang]}</span></div>
          <p>{a['card'][lang]}</p>
          <span class="more">{t['learn']} {icon('arrow')}</span>
        </div>
      </a>""")
    cards.append(f"""<div class="app-card soon reveal">
        <div class="soon-orbs" aria-hidden="true"><span></span><span></span><span></span></div>
        <h3>{c['soon_h']}</h3>
        <p>{c['soon_p']}</p>
      </div>""")
    principles = "".join(
        f'<div class="principle reveal"><div class="ico">{icon(i)}</div><h3>{h}</h3><p>{p}</p></div>'
        for i, h, p in c["principles"]
    )
    facts = "".join(
        f'<div class="fact">{icon(i)}<div><b>{h}</b><span>{p}</span></div></div>' for i, h, p in c["facts"]
    )
    main = f"""<section class="hero" aria-labelledby="hero-title">
  <div class="hero-media" aria-hidden="true">
    <img src="/assets/video/hero-poster.webp" alt="" width="1280" height="720" fetchpriority="high">
    <video muted loop playsinline preload="none" poster="/assets/video/hero-poster.webp">
      <source data-src="/assets/video/hero.webm" type="video/webm">
      <source data-src="/assets/video/hero.mp4" type="video/mp4">
    </video>
  </div>
  <div class="wrap">
    <div class="hero-copy">
      <span class="eyebrow">{c['eyebrow']}</span>
      <h1 id="hero-title">{c['h1']}</h1>
      <p class="lead">{c['lead']}</p>
      <div class="actions">
        <a class="btn btn-primary" href="#apps">{c['cta1']} {icon('arrow')}</a>
        <a class="btn btn-ghost" href="#contact">{icon('mail')} {c['cta2']}</a>
      </div>
    </div>
  </div>
</section>

<section class="section" id="apps" aria-labelledby="apps-title">
  <div class="wrap">
    <div class="section-head reveal">
      <span class="eyebrow">{c['apps_eyebrow']}</span>
      <h2 id="apps-title">{c['apps_h2']}</h2>
      <p>{c['apps_p']}</p>
    </div>
    <div class="apps">
      {''.join(cards)}
    </div>
  </div>
</section>

<section class="section" aria-labelledby="how-title" style="padding-top:0">
  <div class="wrap">
    <div class="section-head reveal">
      <span class="eyebrow">{c['how_eyebrow']}</span>
      <h2 id="how-title">{c['how_h2']}</h2>
      <p>{c['how_p']}</p>
    </div>
    <div class="principles">{principles}</div>
  </div>
</section>

<section class="section" id="studio" aria-labelledby="studio-title" style="padding-top:0">
  <div class="wrap">
    <div class="band reveal">
      <div>
        <span class="eyebrow">{c['studio_eyebrow']}</span>
        <h2 id="studio-title">{c['studio_h2']}</h2>
        <p>{c['studio_p1']}</p>
        <p style="margin:0">{c['studio_p2']}</p>
      </div>
      <div class="facts">{facts}</div>
    </div>
  </div>
</section>

<section class="section contact" id="contact" aria-labelledby="contact-title" style="padding-top:0">
  <div class="wrap reveal">
    <span class="eyebrow">{c['contact_eyebrow']}</span>
    <h2 id="contact-title">{c['contact_h2']}</h2>
    <p>{c['contact_p']}</p>
    <a class="btn btn-primary mail" href="mailto:{EMAIL}">{icon('mail')} {EMAIL}</a>
  </div>
</section>"""
    return page(lang, "home", c["title"], c["desc"], main, preload="/assets/video/hero-poster.webp")


def app_page(app: dict, lang: str) -> str:
    key = app["key"]
    c = APP_PAGES[key][lang]
    t = UI[lang]
    flip = " flip" if app["flip"] else ""
    steps = "".join(f"<li><b>{h}</b>{p}</li>" for h, p in c["steps"])
    feats = "".join(
        f'<div class="feature reveal"><div class="ico">{icon(i)}</div><h3>{h}</h3><p>{p}</p></div>'
        for i, h, p in c["features"]
    )
    cta2 = ""
    if c.get("cta2"):
        cta2 = f'<a class="btn btn-ghost" href="{URLS["quevia_privacy"][lang]}">{icon("lock")} {c["cta2"]}</a>'
    shots = ""
    if key == "quevia":
        imgs = "".join(
            f'<img src="/assets/img/shots/quevia-{lang}-{i}.webp" alt="" width="540" height="960" loading="lazy" decoding="async">'
            for i in range(1, 9)
        )
        shots = f"""
<section class="section" aria-labelledby="shots-title" style="padding-top:0">
  <div class="wrap">
    <div class="section-head reveal">
      <span class="eyebrow">{c['shots_eyebrow']}</span>
      <h2 id="shots-title">{c['shots_h2']}</h2>
    </div>
    <div class="shots-wrap reveal"><div class="shots" tabindex="0" role="region" aria-label="Screenshots">{imgs}</div></div>
  </div>
</section>"""
    if key == "quevia":
        privacy_links = (
            f'<div class="legal-links"><a class="btn btn-ghost" href="{URLS["quevia_privacy"][lang]}">{icon("lock")} {t["q_privacy"]}</a>'
            f'<a class="btn btn-ghost" href="{URLS["legal"][lang]}">{t["legal"]}</a></div>'
        )
    else:
        privacy_links = f'<div class="legal-links"><a class="btn btn-ghost" href="mailto:{EMAIL}">{icon("mail")} {t["contact"]}</a></div>'
    main = f"""<section class="hero app{flip} t-{key}" aria-labelledby="hero-title">
  <div class="hero-media" aria-hidden="true">
    <img src="/assets/img/{app['art']}.webp" srcset="/assets/img/{app['art']}-800.webp 800w, /assets/img/{app['art']}.webp 1536w" sizes="100vw" alt="" width="1536" height="1024" fetchpriority="high">
  </div>
  <div class="wrap">
    <div class="hero-copy">
      <div class="app-id">
        <img src="{app['icon']}" alt="{app['name']}" width="72" height="72">
        <div><div class="chips">{chip(app['status'], lang)}<span class="chip">{app['platforms'][lang]}</span></div></div>
      </div>
      <h1 id="hero-title" style="margin-top:22px">{c['h1']}</h1>
      <p class="lead">{c['lead']}</p>
      <div class="actions">
        <a class="btn btn-primary" href="#how">{c['cta1']} {icon('arrow')}</a>
        {cta2}
      </div>
    </div>
  </div>
</section>

<section class="section t-{key}" id="how" aria-labelledby="how-title">
  <div class="wrap">
    <div class="note reveal" style="margin-bottom:clamp(48px,7vw,80px)">{icon('info')}<p>{c['note']}</p></div>
    <div class="split">
      <div class="reveal">
        <span class="eyebrow">{c['how_eyebrow']}</span>
        <h2 id="how-title">{c['how_h2']}</h2>
        <p>{c['how_p']}</p>
      </div>
      <ol class="steps reveal">{steps}</ol>
    </div>
  </div>
</section>
{shots}
<section class="section t-{key}" aria-labelledby="feat-title" style="padding-top:0">
  <div class="wrap">
    <div class="section-head reveal">
      <span class="eyebrow">{c['feat_eyebrow']}</span>
      <h2 id="feat-title">{c['feat_h2']}</h2>
    </div>
    <div class="features">{feats}</div>
  </div>
</section>

<section class="section" aria-labelledby="privacy-title" style="padding-top:0">
  <div class="wrap">
    <div class="band reveal">
      <div>
        <span class="eyebrow">{c['privacy_eyebrow']}</span>
        <h2 id="privacy-title">{c['privacy_h2']}</h2>
        <p style="margin:0">{c['privacy_p']}</p>
      </div>
      <div>{privacy_links}</div>
    </div>
  </div>
</section>"""
    return page(lang, key, c["title"], c["desc"], main, preload=f"/assets/img/{app['art']}.webp")


def legal_page(key: str, lang: str, fragment: str, title: str, desc: str) -> str:
    body = (SRC / "legal" / fragment).read_text(encoding="utf-8").strip()
    main = f'<article class="doc">\n<div class="wrap">\n{body}\n</div>\n</article>'
    return page(lang, key, title, desc, main)


def not_found() -> str:
    main = """<article class="doc" style="min-height:70vh">
<div class="wrap">
<span class="eyebrow">404</span>
<h1>This page took a side quest.</h1>
<p class="lead">We couldn’t find what you were looking for. <span lang="de">Diese Seite gibt es leider nicht.</span></p>
<p><a class="btn btn-primary" href="/">Kroess Labs home</a> <a class="btn btn-ghost" href="/de/" lang="de">Startseite (Deutsch)</a></p>
</div>
</article>"""
    return page("en", "home", "Page not found · Kroess Labs", "This page does not exist.", main).replace(
        '<link rel="canonical" href="https://kroesslabs.de/">\n', '<meta name="robots" content="noindex">\n'
    )


def intern_page() -> str:
    """Password-protected internal page. German only, not indexed, not in the sitemap."""
    extra_head, main = intern.page_parts(INTERN_VERSION)
    out = page("de", "home", "Intern · Kroess Labs", "Interner Bereich von Kroess Labs.", main)
    out = re.sub(r'<link rel="(canonical|alternate)"[^>]*>\n', "", out)
    out = re.sub(r'<meta property="og:url"[^>]*>\n', "", out)
    return out.replace("</head>", '<meta name="robots" content="noindex, nofollow">\n' + extra_head + "</head>", 1)


# --------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------


def write(url: str, content: str) -> None:
    path = ROOT / (url.strip("/") + "/index.html" if url.strip("/") else "index.html")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print("wrote", path.relative_to(ROOT))


def sitemap() -> str:
    rows = []
    for key, by_lang in URLS.items():
        for lang, url in by_lang.items():
            alts = "".join(
                f'<xhtml:link rel="alternate" hreflang="{l}" href="{SITE}{u}"/>' for l, u in by_lang.items()
            )
            rows.append(f"<url><loc>{SITE}{url}</loc>{alts}</url>")
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
        + "\n".join(rows)
        + "\n</urlset>\n"
    )


def main() -> None:
    global INTERN_VERSION
    INTERN_VERSION = intern.build_data(ROOT)
    if INTERN_VERSION:
        write(INTERN_URL, intern_page())
    for lang in ("en", "de"):
        write(URLS["home"][lang], home_page(lang))
        for app in APPS:
            write(URLS[app["key"]][lang], app_page(app, lang))
    for key, lang, fragment, title, desc in LEGAL_PAGES:
        write(URLS[key][lang], legal_page(key, lang, fragment, title, desc))
    (ROOT / "404.html").write_text(not_found(), encoding="utf-8")
    print("wrote 404.html")
    (ROOT / "sitemap.xml").write_text(sitemap(), encoding="utf-8")
    (ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n", encoding="utf-8")
    print("wrote sitemap.xml, robots.txt")


if __name__ == "__main__":
    main()
