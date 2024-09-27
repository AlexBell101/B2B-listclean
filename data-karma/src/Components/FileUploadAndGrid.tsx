import React, { useState } from 'react';
import FileUploader from './FileUpload/FileUpload';
import DataGridDisplay from './Grid/Grid';
import './FileUploadAndGrid.css';

const FileUploadAndGrid = () => {
    const [columns, setColumns] = useState([])  ;
    const [rows, setRows] = useState([]);

    const handleDataParsed = (data) => {
        if (data.length > 0) {
            const [headerRow, ...dataRows] = data;

            const gridColumns = headerRow.map((header, index) => ({
                key: index.toString(),
                name: header || `Column ${index + 1}`
            }));

            const gridRows = dataRows.map((row) => {
                const rowData = {};
                row.forEach((cell, index) => {
                    rowData[index.toString()] = cell;
                });
                return rowData;
            });

            setColumns(gridColumns);
            setRows(gridRows);
        }
    };

    return (
        <div className="file-upload-grid-container">
            <FileUploader onDataParsed={handleDataParsed} />
            <DataGridDisplay columns={columns} rows={rows} />
        </div>
    );
};

export default FileUploadAndGrid;
