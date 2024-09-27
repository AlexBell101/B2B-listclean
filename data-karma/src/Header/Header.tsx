import React, { useContext, useState } from 'react';
import './Header.css';
import logo from '../assets/logo-nobg.png';
import Login from '../Login/Login';
import { Link, useNavigate } from 'react-router-dom';
import PocketBaseContext from '../PocketBaseContext';



// Define the props for the Header component (if any in the future)
interface HeaderProps { }

const Header: React.FC<HeaderProps> = () => {
    const pb = useContext(PocketBaseContext);
    const navigate = useNavigate(); // Hook for navigating

    const handleLogout = () => {
        pb.authStore.clear();
        navigate("/");
    };

    return (
        <header className="header">
            <div className="logo">
                <img src={logo} alt="Logo" />
            </div>
            <nav className="nav">
                <button className="nav-button">Email Karma</button>
                <button className="nav-button">List Karma</button>
                {pb.authStore.isValid ? (
                    <button className="nav-button" onClick={() => handleLogout()}>Logout</button>
                ) : (
                    <Link className="nav-button" to="/login">Sign In</Link>
                )}
            </nav>
        </header>
    );
};

export default Header;
