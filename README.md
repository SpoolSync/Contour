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

- People create an account with an email and password. The same Pixora account works across Pixora apps.
- Data is saved on the device first and synced to the Pixora cloud (Firebase, database located in Toronto). The app keeps working offline after the first login and syncs when the connection returns.
- A member can give one trainer read-only access by entering the trainer's email. The trainer sees the member's current profile and cannot change it.
- `data/cloud.js` holds the Firebase web config. It is not a secret; access is controlled by the security rules in the Firebase console.
- The Firebase scripts in `vendor/` are copied from the `firebase` npm package (version 10.12.2) so the app can start offline.
- Logging food from a photo and photo body scans need the Claude-hosted version of the app and are hidden here.
- When you update the files, change `VERSION` at the top of `sw.js` so installed phones fetch the new copy.

## Data sources

- Exercises: [free-exercise-db](https://github.com/yuhonas/free-exercise-db), public domain.
- Foods: [USDA FoodData Central](https://fdc.nal.usda.gov/), SR Legacy, public domain, plus a short list of common dishes with approximate values.
- BMI and waist thresholds: Health Canada body weight classification and the WHO expert consultation on Asian populations.

This app gives general fitness guidance for adults. It is not medical advice.
