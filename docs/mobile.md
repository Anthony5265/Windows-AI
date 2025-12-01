# Mobile Pairing

The Windows AI mobile apps can pair with the Actions API to enable remote control.

## Pairing a Device
1. Send a POST request to `/api/mobile/pair` with a JSON body containing a unique `deviceId`.
2. The server returns a pairing `token` that is valid for one hour.
3. Store the token securely on the device.

```bash
curl -X POST http://localhost:3000/api/mobile/pair \
  -H "content-type: application/json" \
  -d '{"deviceId":"device-123"}'
```

## Sending Remote Commands
Use the pairing token to issue commands.

```bash
curl -X POST http://localhost:3000/api/mobile/command \
  -H "content-type: application/json" \
  -d '{"token":"<token>","action":"get_system_info"}'
```

The server executes the requested action and returns the result.
