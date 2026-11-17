# Contour Body Tracker

A fitness tracker that runs entirely in the browser: food logging, body scans, a body-part focus plan, progress charts, weekly and monthly reports, and trainer sharing. It installs to a phone's home screen and works offline.

## Put it online with GitHub Pages

1. Create a new **public** repository on github.com (for example `contour`).
2. Upload every file and folder from this package to the repository root, keeping the `data` folder. The hidden `.nojekyll` file should go too.
3. In the repository, open **Settings → Pages**. Under "Build and deployment", choose **Deploy from a branch**, branch **main**, folder **/ (root)**, and save.
4. After a minute or two the app is live at `https://<your-username>.github.io/<repository-name>/`.

## Use it on a phone

- **iPhone:** open the address in Safari, tap Share, then **Add to Home Screen**.
- **Android:** open it in Chrome, tap the menu, then **Install app** or **Add to Home screen**.

It then opens full screen like an app and keeps working without a connection.

## What to know

- The app is invite-only. People need an access code to get in. The codes are not stored in this repository, only locked copies of the key they open.
- Each person's data stays in the browser on their own device. Clearing site data or switching phones starts them fresh. Nothing is sent to a server.
- Trainer sharing works by file: a member creates a share file for one trainer, and only that trainer can open it.
- Logging food from a photo, photo body scans and the shared community food list need the Claude-hosted version of the app and are hidden here.
- When you update the files, change `VERSION` at the top of `sw.js` so installed phones fetch the new copy.

## Data sources

- Exercises: [free-exercise-db](https://github.com/yuhonas/free-exercise-db), public domain.
- Foods: [USDA FoodData Central](https://fdc.nal.usda.gov/), SR Legacy, public domain, plus a short list of common dishes with approximate values.
- BMI and waist thresholds: Health Canada body weight classification and the WHO expert consultation on Asian populations.

This app gives general fitness guidance for adults. It is not medical advice.
