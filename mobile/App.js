import React, { useState } from 'react';
import { View, Text, TextInput, Button, Alert } from 'react-native';
import { loginRequest, pairRequest } from './api';

export default function App() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loggedIn, setLoggedIn] = useState(false);
  const [deviceId, setDeviceId] = useState('');
  const [token, setToken] = useState(null);

  const login = async () => {
    try {
      await loginRequest(username, password);
      setLoggedIn(true);
    } catch (err) {
      Alert.alert('Login failed', err.message);
    }
  };

  const pair = async () => {
    try {
      const received = await pairRequest(deviceId);
      setToken(received);
    } catch (err) {
      Alert.alert('Pairing failed', err.message);
    }
  };

  if (!loggedIn) {
    return (
      <View style={{ padding: 20 }}>
        <Text>Login</Text>
        <TextInput placeholder="Username" value={username} onChangeText={setUsername} />
        <TextInput
          placeholder="Password"
          secureTextEntry
          value={password}
          onChangeText={setPassword}
        />
        <Button title="Login" onPress={login} />
      </View>
    );
  }

  if (!token) {
    return (
      <View style={{ padding: 20 }}>
        <Text>Pair with Desktop</Text>
        <TextInput placeholder="Device ID" value={deviceId} onChangeText={setDeviceId} />
        <Button title="Pair" onPress={pair} />
      </View>
    );
  }

  return (
    <View style={{ padding: 20 }}>
      <Text>Paired as {deviceId}</Text>
      <Text>Token: {token}</Text>
    </View>
  );
}
