import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { useNavigation } from '@react-navigation/native';

const HomeScreen = () => {
    const navigation = useNavigation(); // Get navigation object to navigate to new page

    return (
        <View style={styles.container}>
            <Text style={styles.subheading}>Empower Your Marketing Team</Text>
            <Text style={styles.heading}>Karmic B2B AI tools</Text>
            <Text style={styles.subheading}>
                DataKarma.ai empowers marketers, operations ninjas, and data scientists to quickly and intelligently create relevant nurture emails and prepare raw data lists for upload to CRM and Marketing Automation platforms.            </Text>
            <TouchableOpacity style={styles.button}
                onPress={() => navigation.navigate('ListKarma')}

            >
                <Text style={styles.buttonText}>List Karma</Text>
            </TouchableOpacity>
        </View>
    );
};

const styles = StyleSheet.create({
    container: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        backgroundColor: '#1B1B1B', // Dark background
        paddingHorizontal: 20, // Padding to keep text from touching edges
    },
    heading: {
        fontSize: 32, // Large, bold text
        fontWeight: 'bold',
        color: '#FFFFFF', // White text
        textAlign: 'center', // Center the heading
        marginBottom: 20, // Space between heading and subheading
    },
    subheading: {
        fontSize: 18, // Smaller subheading text
        color: '#FFFFFF', // White text
        textAlign: 'center',
        lineHeight: 24, // Better readability
    },
    button: {
        backgroundColor: '#007BFF', // Blue background
        paddingVertical: 15, // Vertical padding
        paddingHorizontal: 40, // Horizontal padding
        borderRadius: 25, // Rounded corners
        marginTop: 30, // Space between text and button
    },
    buttonText: {
        color: '#FFFFFF', // White text
        fontSize: 18,
        fontWeight: 'bold',
        textAlign: 'center',
    },
});
export default HomeScreen;
