# Mobile Companion Setup

This guide outlines how to try the placeholder mobile companion app and pair it with the desktop Control Center.

## Prerequisites
- Node.js and npm
- An emulator or device capable of running React Native apps

## Running the App
1. Navigate to the `mobile/` directory and install dependencies:
   ```sh
   npm install
   npm start
   ```
2. Use your emulator or the Expo app to open the development server.
3. Sign in with any credentials. Authentication is not yet wired up.

## Pairing with the Desktop
1. In the desktop Control Center, choose **Pair Mobile** to display a secure token or QR code.
2. Enter the token into the mobile app's pairing screen.
3. Once paired, the token can be used to send remote commands through the Actions API.

## API Overview
- `POST /api/mobile/pair` → obtain a pairing token for a device.
- `POST /api/mobile/command` → execute an action on the paired desktop.

These endpoints are provided by the `apps/actions-api` service and are still under active development.
