import React, { useState } from 'react';
import { View, Text, TextInput, Button } from 'react-native';

export default function App() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loggedIn, setLoggedIn] = useState(false);
  const [deviceId, setDeviceId] = useState('');
  const [token, setToken] = useState(null);

  const login = () => {
    // Placeholder auth
    setLoggedIn(true);
  };

  const pair = async () => {
    // Placeholder API call
    setToken('demo-token');
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
