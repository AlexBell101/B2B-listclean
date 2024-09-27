import React from 'react';
import ReactDataGrid from 'react-data-grid';

const DataGridDisplay = ({ columns, rows }) => {
    return (
        <div>
            {columns.length > 0 && (
                <div className="grid-container">
                    <ReactDataGrid
                        columns={columns}
                        rows={rows}
                        defaultColumnOptions={{
                            resizable: true,
                        }}
                    />
                </div>
            )}
        </div>
    );
};

export default DataGridDisplay;
