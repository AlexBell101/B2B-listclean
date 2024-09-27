import React from 'react';
import Papa from 'papaparse';
import * as XLSX from 'xlsx';

const FileUploader = ({ onDataParsed }) => {
    const handleFileUpload = (event) => {
        const file = event.target.files[0];
        const reader = new FileReader();
        const fileExtension = file.name.split('.').pop().toLowerCase();

        if (fileExtension === 'csv') {
            reader.onload = () => {
                const text = reader.result;
                Papa.parse(text, {
                    header: true,
                    complete: (result) => {
                        onDataParsed(result.data);
                    },
                    skipEmptyLines: true,
                });
            };
            reader.readAsText(file);
        } else if (fileExtension === 'xlsx' || fileExtension === 'xls') {
            reader.onload = () => {
                const data = new Uint8Array(reader.result);
                const workbook = XLSX.read(data, { type: 'array' });
                const sheetName = workbook.SheetNames[0];
                const sheet = workbook.Sheets[sheetName];
                const jsonData = XLSX.utils.sheet_to_json(sheet, { header: 1 });

                onDataParsed(jsonData);
            };
            reader.readAsArrayBuffer(file);
        } else {
            alert('Please upload a valid CSV or Excel file.');
        }
    };

    return (
        <div>
            <h2>Upload CSV or Excel File</h2>
            <input
                type="file"
                accept=".csv, .xlsx, .xls"
                onChange={handleFileUpload}
            />
        </div>
    );
};

export default FileUploader;
