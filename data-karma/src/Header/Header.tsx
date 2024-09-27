import React from 'react';
import './Header.css';
import logo from '../assets/logo-nobg.png';


// Define the props for the Header component (if any in the future)
interface HeaderProps { }

const Header: React.FC<HeaderProps> = () => {
    return (
        <header className="header">
            <div className="logo">
                <img src={logo} alt="Logo" />
            </div>
            <nav className="nav">
                <button className="nav-button">Email Karma</button>
                <button className="nav-button">List Karma</button>
                <button className="nav-button">Sign In</button>
            </nav>
        </header>
    );
};

export default Header;
