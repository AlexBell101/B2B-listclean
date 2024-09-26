import React, { useState } from 'react';
import { parsePhoneNumberFromString } from 'libphonenumber-js';

// Papa parse or whatever output...
const DataTable = ({ parsedData }) => {
    const [data, setData] = useState(parsedData.slice(1)); // no headers
    const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });
    const [columns, setColumns] = useState(parsedData[0].map((header, index) => ({
        key: `column_${index}`,
        label: header,
    }))); // Initialize columns from the first row (headers)

    // FIXME: can probably cover 90% with this list but mgiht need more
    const personalDomains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'aol.com', 'outlook.com'];

    const countryToCode = (countryName) => {
        const countryCodes = {
            'United States': 'US',
            'Canada': 'CA',
            'United Kingdom': 'GB',
            //FIXME: need to find all mappings 
        };
        return countryCodes[countryName] || countryName; A
    };


    const cleanPhone = (phone) => {
        const parsedPhone = parsePhoneNumberFromString(phone, 'US');
        return parsedPhone ? parsedPhone.format('E.164') : phone;
    };

    const extractEmailDomain = (data) => {
        if (data[0].includes('Email')) {
            const emailIndex = data[0].indexOf('Email');
            data.forEach((row, index) => {
                if (index !== 0 && row[emailIndex]) {
                    const email = row[emailIndex];
                    const domain = email.includes('@') ? email.split('@')[1] : '';
                    row.push(domain); 
                }
            });
            data[0].push('Domain');
        }
        return data;
    };

    const classifyEmailType = (data) => {
        if (data[0].includes('Domain')) {
            const domainIndex = data[0].indexOf('Domain'); // probably need more than one case
            data.forEach((row, index) => {
                if (index !== 0) {
                    const domain = row[domainIndex];
                    const emailType = personalDomains.includes(domain) ? 'Personal' : 'Business';
                    row.push(emailType); 
                }
            });
            data[0].push('Email Type'); 
        }
        return data;
    };

    const removePersonalEmails = (data) => {
        if (data[0].includes('Domain')) {
            const domainIndex = data[0].indexOf('Domain');
            return data.filter((row, index) => index === 0 || !personalDomains.includes(row[domainIndex]));
        }
        return data;
    };

    const splitAddress2 = (data) => {
        if (data[0].includes('Address')) {
            const addressIndex = data[0].indexOf('Address');
            data.forEach((row, index) => {
                if (index !== 0) {
                    const address = row[addressIndex];
                    const address1 = address.split(/\b(Apt|Unit|Suite)\b/i)[0].trim();
                    const address2Match = address.match(/\b(Apt|Unit|Suite)\b.*$/i);
                    const address2 = address2Match ? address2Match[0] : '';
                    row.push(address1);
                    row.push(address2);
                }
            });
            data[0].push('Address 1');
            data[0].push('Address 2');
        }
        return data;
    };

    const splitCityState = (data) => {
        if (data[0].includes('City_State')) {
            const cityStateIndex = data[0].indexOf('City_State');
            data.forEach((row, index) => {
                if (index !== 0) {
                    const [city, state] = row[cityStateIndex].split(',').map(item => item.trim());
                    row.push(city);
                    row.push(state);
                }
            });
            data[0].push('City');
            data[0].push('State');
        }
        return data;
    };

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

        </div>
    );
};

export default DataTable;
