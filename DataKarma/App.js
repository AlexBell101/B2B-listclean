import { StatusBar } from 'expo-status-bar';
import { ImageBackground, Image, StyleSheet, Text, View } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import HomeScreen from './HomeScreen'; // Import your screen here
import { createDrawerNavigator } from '@react-navigation/drawer';
import ListKarmaScreen from './ListKarmaScreen';


const Stack = createStackNavigator();
const Drawer = createDrawerNavigator();


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

const DrawerNavigator = () => {
  return (
    <Drawer.Navigator initialRouteName="ListKarma">
      <Drawer.Screen name="List Karma" component={ListKarmaScreen} />
    </Drawer.Navigator>
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
          component={DrawerNavigator} 
          options={{
            headerShown: false, 
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
