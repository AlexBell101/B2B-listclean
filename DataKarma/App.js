import { StatusBar } from 'expo-status-bar';
import { ImageBackground, Image, StyleSheet, Text, View } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import ListKarmaScreen from './ListKarmaScreen';
import HomeScreen from './HomeScreen';
//import CleanupOptionsDrawer from './CleanupOptionsDrawer';


const Stack = createStackNavigator();


// static
const LogoTitle = () => {
  return (
    <View style={styles.logoContainer}>
      <Image
        source={require('./assets/logo-nobg.png')}
        style={styles.logo}
        resizeMode="contain"
      />
    </View>
  );
};


export default function App() {
  return (
    <NavigationContainer>
      <Stack.Navigator>
        <Stack.Screen
          name="Home"
          component={HomeScreen}
          options={{
            headerTitle: (props) => <LogoTitle {...props} />,
            headerTitleAlign: 'center',
            headerStyle: styles.header,
          }}
        />
        <Stack.Screen
          name="ListKarma"
          component={ListKarmaScreen}
          options={{
            headerShown: true,
          }}
        />
      </Stack.Navigator>
    </NavigationContainer>
  );
}

const styles = StyleSheet.create({
  header: {
    backgroundColor: '#1B1B1B',
    shadowColor: 'transparent',
  },
  logoContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  logo: {
    width: 120,
    height: 40,
  },
});
