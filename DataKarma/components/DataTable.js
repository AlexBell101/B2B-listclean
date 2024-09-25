import React, { useState } from 'react';

// Papa parse or whatever output...
const DataTable = ({ parsedData }) => {
    const [data, setData] = useState(parsedData.slice(1)); // no headers
    const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });
    const [columns, setColumns] = useState(parsedData[0].map((header, index) => ({
        key: `column_${index}`,
        label: header,
    }))); // Initialize columns from the first row (headers)

    // const columns = parsedData[0].map((header, index) => ({
    //     key: `column_${index}`,
    //     label: header,
    // }));

    const handleSort = (key) => {
        let direction = 'asc';
        if (sortConfig.key === key && sortConfig.direction === 'asc') {
            direction = 'desc';
        }
        const sortedData = [...data].sort((a, b) => {
            if (a[key] < b[key]) return direction === 'asc' ? -1 : 1;
            if (a[key] > b[key]) return direction === 'asc' ? 1 : -1;
            return 0;
        });
        setSortConfig({ key, direction });
        setData(sortedData);
    };

    // commented out but probably worth using later for manipulation
    const handleAddColumn = () => {
        const newColumnKey = `column_${columns.length}`;
        const newColumnLabel = `Column ${columns.length + 1}`;

        const newColumns = [...columns, { key: newColumnKey, label: newColumnLabel }];
        setColumns(newColumns);
        const updatedData = data.map(row => [...row, '']);
        setData(updatedData);
    };

    const handleAddRow = () => {
        const newRow = columns.map(() => '');
        setData([...data, newRow]);
    };

    const handleAddCol = () => {
        const newCol = r
    }

    const handleCellChange = (rowIndex, columnIndex, value) => {
        const updatedData = data.map((row, index) => {
            if (index === rowIndex) {
                const updatedRow = [...row];
                updatedRow[columnIndex] = value;
                return updatedRow;
            }
            return row;
        });
        setData(updatedData);
    };

    return (
        <div>
            {/* Table */}
            <table border="1" style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                    <tr>
                        {columns.map((column, index) => (
                            <th
                                key={index}
                                onClick={() => handleSort(index)}
                                style={{ cursor: 'pointer' }}
                            >
                                {column.label}
                                {sortConfig.key === index && (
                                    <span>{sortConfig.direction === 'asc' ? ' 🔼' : ' 🔽'}</span>
                                )}
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {data.map((row, rowIndex) => (
                        <tr key={rowIndex}>
                            {row.map((cell, cellIndex) => (
                                <td key={cellIndex}>
                                    <input
                                        type="text"
                                        value={cell}
                                        onChange={(e) => handleCellChange(rowIndex, cellIndex, e.target.value)}
                                        style={{ width: '100%' }}
                                    />
                                </td>
                            ))}
                        </tr>
                    ))}
                </tbody>
            </table>

            {/* <button onClick={handleAddRow} style={{ marginTop: '10px' }}>
                Add Row
            </button>
            <button onClick={handleAddColumn} style={{ marginTop: '10px', marginRight: '10px' }}>
                Add Column
            </button> */}
        </div>
    );
};

export default DataTable;
