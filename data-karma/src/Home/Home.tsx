import React from 'react';
import './Home.css'; // Import the CSS for styling
import REACT_SVG from '../assets/react.svg';
import Header from '../Header/Header';
import { Link } from 'react-router-dom';

const Home: React.FC = () => {
    return (
        <div className="home-container">
            <Header></Header>
            <div className="text-section">
                <h1>Empower Your Marketing Team</h1>
                <p>DataKarma.ai empowers marketers, operations ninjas, and data scientists to quickly and intelligently create relevant nurture emails and prepare raw data lists for upload to CRM and Marketing Automation platforms.</p>
                {/* <button className="btn">List Karma</button> */}
                <Link className="btn" to="/listkarma">List Karma</Link>
                <button className="btn">Email Karma</button>
            </div>
            <div className="image-section">
                <img src={REACT_SVG} alt="Data Tools Visualization" />
            </div>
        </div>
    );
};

export default Home;
