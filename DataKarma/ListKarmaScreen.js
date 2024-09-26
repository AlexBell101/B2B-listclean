import React, { useState } from 'react';
import { ScrollView, View, Text, TouchableOpacity, StyleSheet, Platform, Button, Switch } from 'react-native';
import * as DocumentPicker from 'expo-document-picker';
import Papa from "papaparse";
import { RadioButton } from 'react-native-paper';
import { Picker } from '@react-native-picker/picker';
import DataTable from './components/DataTable';


const ListKarmaScreen = () => {
    const [latestChangeDate, setLatestChangeDate] = useState(null); // store the last change date
    const [fileContent, setFileContent] = useState(null); // To store parsed content
    const [outputFormat, setOutputFormat] = useState('csv');
    const [countryFieldFormat, setCountryFieldFormat] = useState('leave');
    const [standardisePhoneNumbers, setStandardisePhoneNumbers] = useState(false);
    const [capitalizeLetterOfNames, setCapitalizeLetterOfNames] = useState(false);
    const [classifyEmails, setClassifyEmails] = useState(false);
    const [extractEmailDomains, setExtractEmailDomains] = useState(false);
    const [removeRowsWithPersonalEmails, setremoveRowsWithPersonalEmails] = useState(false);
    const [separateAddressFields, setSeparateAddressFields] = useState(false);
    const [splitCombinedCityAndState, setSplitCombinedCityAndState] = useState(false);

    const [tableHistory, setTableHistory] = useState([]);


    const UploadAListButton = () => {

        return (
            <TouchableOpacity style={styles.button} onPress={handleFilePicker}>
                <Text style={styles.buttonText}>Upload a List</Text>
            </TouchableOpacity>
        );

    };

    const handleApply = () => {
        if (fileContent) {
            const currentDate = new Date().toLocaleString(); // Get current date and time
            const newTableEntry = {
                data: fileContent,
                timestamp: currentDate,
            };
            setTableHistory([...tableHistory, newTableEntry]); // Add new table to history
        }
    };

    const handleFilePicker = async () => {
        try {
            const res = await DocumentPicker.getDocumentAsync({
                type: "text/csv", // Any file type
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
                    const fileUri = res.uri;

                    const fileContentString = await FileSystem.readAsStringAsync(fileUri);

                    const parsedData = Papa.parse(fileContentString, {
                        header: true,
                        skipEmptyLines: true,
                    });

                    console.log('Parsed CSV Data:', parsedData.data);

                    if (parsedData.errors.length) {
                        console.error('Error parsing CSV:', parsedData.errors);
                        Alert.alert('Error', 'There was an issue parsing the CSV file.');
                        return;
                    }

                    setFileContent(parsedData.data); // Save parsed data
                    Alert.alert('Success', 'CSV file parsed and displayed.');
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
            {/* Left Panel - Cleanup Options */}
            <View style={styles.leftPanel}>
                <Text style={styles.title}>Cleanup Options</Text>

                {/* Output format radio buttons */}
                <Text style={styles.subTitle}>Select output format</Text>
                <RadioButton.Group onValueChange={value => setOutputFormat(value)} value={outputFormat}>
                    <View style={styles.radioContainer}>
                        <RadioButton value="csv" />
                        <Text>CSV</Text>
                    </View>
                    <View style={styles.radioContainer}>
                        <RadioButton value="excel" />
                        <Text>Excel</Text>
                    </View>
                    <View style={styles.radioContainer}>
                        <RadioButton value="txt" />
                        <Text>TXT</Text>
                    </View>
                </RadioButton.Group>

                {/* Selection field */}
                <Text style={styles.subTitle}>Selection Options</Text>
                <View style={styles.pickerContainer}>
                    <Picker
                        selectedValue={countryFieldFormat}
                        onValueChange={(itemValue) => setCountryFieldFormat(itemValue)}
                    >
                        <Picker.Item label="Leave as-is" value="leave" />
                        <Picker.Item label="Long Form" value="long" />
                        <Picker.Item label="Country Code" value="countryCode" />
                    </Picker>
                </View>

                {/* Checkbox for email classification */}
                <View style={styles.checkboxContainer}>
                    <Text>Classify emails as Personal or Business?</Text>
                    <Switch
                        value={classifyEmails}
                        onValueChange={(newValue) => setClassifyEmails(newValue)}
                    />
                </View>


                {/* Checkbox for email classification */}
                <View style={styles.checkboxContainer}>
                    <Text>Capitalize First Letter of Names?</Text>
                    <Switch
                        value={capitalizeLetterOfNames}
                        onValueChange={(newValue) => setCapitalizeLetterOfNames(newValue)}
                    />
                </View>

                {/* Checkbox for email classification */}
                <View style={styles.checkboxContainer}>
                    <Text>Standardize Phone Numbers?</Text>
                    <Switch
                        value={standardisePhoneNumbers}
                        onValueChange={(newValue) => setStandardisePhoneNumbers(newValue)}
                    />
                </View>

                {/* Checkbox for email classification */}
                <View style={styles.checkboxContainer}>
                    <Text>Extract Email Domains?</Text>
                    <Switch
                        value={extractEmailDomains}
                        onValueChange={(newValue) => setExtractEmailDomains(newValue)}
                    />
                </View>

                {/* Checkbox for email classification */}
                <View style={styles.checkboxContainer}>
                    <Text>Remove rows with personal Emails?</Text>
                    <Switch
                        value={removeRowsWithPersonalEmails}
                        onValueChange={(newValue) => setremoveRowsWithPersonalEmails(newValue)}
                    />
                </View>

                {/* Checkbox for email classification */}
                <View style={styles.checkboxContainer}>
                    <Text>Separate Address Fields?</Text>
                    <Switch
                        value={separateAddressFields}
                        onValueChange={(newValue) => setSeparateAddressFields(newValue)}
                    />
                </View>

                <View style={styles.checkboxContainer}>
                    <Text>Split Combined City and State Fields?</Text>
                    <Switch
                        value={splitCombinedCityAndState}
                        onValueChange={(newValue) => setSplitCombinedCityAndState(newValue)}
                    />
                </View>

                {/* Apply Button */}
                <Button title="Apply" onPress={handleApply} />
            </View>

            {/* Right Panel - Data Table */}
            <ScrollView style={styles.rightPanel}>
                {fileContent && (
                    <>

                        <Text style={styles.title}>Original Upload:</Text>
                        <DataTable parsedData={fileContent} />
                    </>
                )}
                {tableHistory.length > 0 && (
                    tableHistory.map((table, index) => (
                        <View key={index} style={styles.tableContainer}>
                            <Text style={styles.title}>Alteration #{index}: {table.timestamp}</Text>
                            <DataTable parsedData={table.data} />
                        </View>
                    ))
                )}
                {!fileContent && (
                    <UploadAListButton></UploadAListButton>
                )}
            </ScrollView>
        </View>
    );
};

const styles = StyleSheet.create({
    container: {
        flex: 1,
        flexDirection: 'row',
        padding: 20,
    },
    leftPanel: {
        flex: 0.3,
        paddingRight: 20,
        borderRightWidth: 1,
        borderRightColor: '#ccc',
    },
    rightPanel: {
        flex: 0.7,
        paddingLeft: 20,
    },
    button: {
        backgroundColor: '#007BFF',
        paddingVertical: 15,
        paddingHorizontal: 40,
        borderRadius: 25,
        marginTop: 20,
    },
    buttonText: {
        color: '#FFFFFF',
        fontSize: 18,
        fontWeight: 'bold',
        textAlign: 'center',
    },
    title: {
        fontSize: 24,
        fontWeight: 'bold',
        marginBottom: 20,
    },
    subTitle: {
        fontSize: 18,
        fontWeight: 'bold',
        marginVertical: 10,
    },
    radioContainer: {
        flexDirection: 'row',
        alignItems: 'center',
        marginBottom: 10,
    },
    pickerContainer: {
        borderWidth: 1,
        borderColor: '#ccc',
        borderRadius: 5,
        marginBottom: 20,
    },
    checkboxContainer: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: 20,
    },
});

export default ListKarmaScreen;
