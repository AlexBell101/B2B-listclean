import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Platform } from 'react-native';
import * as DocumentPicker from 'expo-document-picker';

const ListKarmaScreen = () => {
    // Function to handle file selection and logging
    const handleFilePicker = async () => {
        try {
            const res = await DocumentPicker.getDocumentAsync({
                type: 'csv', // Any file type
            });

            if (!res.canceled) {
                let file = res.output[0];
                console.log('File selected:', file.name);

                if (Platform.OS === 'web') {
                    // For web: Use FileReader to read the file
                    const reader = new FileReader();
                    reader.addEventListener(
                        "load",
                        () => {
                            // this will then display a text file
                            console.log(reader.result);
                            //content.innerText = reader.result;
                        },
                        false,
                    );
                    if (file) {
                        reader.readAsText(file);
                    }

                } else {
                    // For mobile (iOS/Android): Use expo-file-system to read the file
                }
            } else {
                console.log('File selection cancelled');
            }
        } catch (error) {
            console.error('Error during file selection:', error);
        }
    };

    return (
        <View style={styles.container}>
            <TouchableOpacity style={styles.button} onPress={handleFilePicker}>
                <Text style={styles.buttonText}>Select and Log File Content</Text>
            </TouchableOpacity>
        </View>

    );
};

const styles = StyleSheet.create({
    container: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        backgroundColor: '#F0F0F0',
    },
    button: {
        backgroundColor: '#007BFF',
        paddingVertical: 15,
        paddingHorizontal: 40,
        borderRadius: 25,
    },
    buttonText: {
        color: '#FFFFFF',
        fontSize: 18,
        fontWeight: 'bold',
        textAlign: 'center',
    },
});

export default ListKarmaScreen;
