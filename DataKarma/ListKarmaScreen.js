import { React, useState } from 'react';
import { ScrollView, View, Text, TouchableOpacity, StyleSheet, Platform } from 'react-native';
import * as DocumentPicker from 'expo-document-picker';
import Papa from "papaparse";

import DataTable from './components/DataTable';

const ListKarmaScreen = () => {
    const [fileContent, setFileContent] = useState(null); // To store parsed content

    const handleFilePicker = async () => {
        try {
            const res = await DocumentPicker.getDocumentAsync({
                type: 'csv', // Any file type
            });

            if (!res.canceled) {
                let file = res.output[0];
                console.log('File selected:', file.name);

                // For web: normal expo-readfile does not work in Web
                if (Platform.OS === 'web') {
                    const reader = new FileReader();
                    reader.addEventListener(
                        "load",
                        () => {
                            console.log(reader.result);
                            Papa.parse(file, {
                                complete: function (results) {
                                    console.log(results);
                                    setFileContent(results.data); // Save parsed data

                                }
                            });
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
            <div style={{ padding: '20px' }}>

                {fileContent && (
                    <h2>Data Preview (Before Cleanup):
                    </h2>
                )}

                {fileContent && (

                    <DataTable parsedData={fileContent} />
                )}
            </div>

            <TouchableOpacity
                style={styles.button}
                onPress={handleFilePicker}
            >
                <Text style={styles.buttonText}>Upload a List</Text>
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
    tableContainer: {
        width: '90%',
        marginTop: 20,
    },
    row: {
        flexDirection: 'row',
        borderBottomWidth: 1,
        borderColor: '#DDD',
    },
    cell: {
        width: 120, // Fixed width for all cells to ensure alignment
        padding: 10,
        borderRightWidth: 1,
        borderColor: '#DDD',
        fontSize: 14,
        color: '#333',
        textAlign: 'center', // Align text to the center of the cell
    },
    headerCell: {
        backgroundColor: '#F5F5F5',
        fontWeight: 'bold',
    },
});

export default ListKarmaScreen;
