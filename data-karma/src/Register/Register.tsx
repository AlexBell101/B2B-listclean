import { Link, useNavigate } from 'react-router-dom';
import './Register.css'; // Assume you include this CSS file
import { useContext, useState } from "react";
import PocketBaseContext from "../PocketBaseContext";


const Register = () => {

    const [email, setEmail] = useState("");
    const [name, setName] = useState("");
    const [password, setPassword] = useState("");
    const [passwordConfirm, setPasswordConfirm] = useState("");
    const [errorText, setErrorText] = useState("");
    const pb = useContext(PocketBaseContext);
    const navigate = useNavigate();

    async function handleSubmit(e) {
        e.preventDefault();
        if (password.length < 10) {
            setErrorText("Password needs to be at least 10 characters");
            return;
        }
        if (password != passwordConfirm) {
            setErrorText("Passwords do not match");
            return;
        }
        try {
            const data = {
                "email": email,
                "emailVisibility": false,
                "password": password,
                "passwordConfirm": passwordConfirm,
                "name": name
            };

            const record = await pb.collection('users').create(data);

            // Automatically login the user
            const authData = await pb.collection('users').authWithPassword(email, password);
            console.log(pb.authStore.isValid);
            console.log(pb.authStore.token);
            console.log(pb.authStore.model.id);
            navigate("/");
        } catch (error) {
            console.error(error);
        }
    }


    return (
        <div className="register-container">
            <div className="card">
                <div className="card-body">
                    <h1 className="card-title">Register</h1>
                    <form className="form" onSubmit={handleSubmit}>
                        <div className="input-container">
                            <label className="input-label">
                                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" className="icon"><path d="M2.5 3A1.5 1.5 0 0 0 1 4.5v.793c.026.009.051.02.076.032L7.674 8.51c.206.1.446.1.652 0l6.598-3.185A.755.755 0 0 1 15 5.293V4.5A1.5 1.5 0 0 0 13.5 3h-11Z" /><path d="M15 6.954 8.978 9.86a2.25 2.25 0 0 1-1.956 0L1 6.954V11.5A1.5 1.5 0 0 0 2.5 13h11a1.5 1.5 0 0 0 1.5-1.5V6.954Z" /></svg>
                                <input required type="email" className="input-field" placeholder="Email" onChange={(e) => { setEmail(e.target.value) }} />
                            </label>
                            <label className="input-label">
                                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" className="icon"><path d="M2.5 3A1.5 1.5 0 0 0 1 4.5v.793c.026.009.051.02.076.032L7.674 8.51c.206.1.446.1.652 0l6.598-3.185A.755.755 0 0 1 15 5.293V4.5A1.5 1.5 0 0 0 13.5 3h-11Z" /><path d="M15 6.954 8.978 9.86a2.25 2.25 0 0 1-1.956 0L1 6.954V11.5A1.5 1.5 0 0 0 2.5 13h11a1.5 1.5 0 0 0 1.5-1.5V6.954Z" /></svg>
                                <input required type="text" className="input-field" placeholder="Name" onChange={(e) => { setName(e.target.value) }} />
                            </label>
                            <label className="input-label">
                                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" className="icon"><path fillRule="evenodd" d="M14 6a4 4 0 0 1-4.899 3.899l-1.955 1.955a.5.5 0 0 1-.353.146H5v1.5a.5.5 0 0 1-.5.5h-2a.5.5 0 0 1-.5-.5v-2.293a.5.5 0 0 1 .146-.353l3.955-3.955A4 4 0 1 1 14 6Zm-4-2a.75.75 0 0 0 0 1.5.5.5 0 0 1 .5.5.75.75 0 0 0 1.5 0 2 2 0 0 0-2-2Z" clipRule="evenodd" /></svg>
                                <input required type="password" className="input-field" placeholder="Password" onChange={(e) => { setPassword(e.target.value) }} />
                            </label>
                            <label className="input-label">
                                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" className="icon"><path fillRule="evenodd" d="M14 6a4 4 0 0 1-4.899 3.899l-1.955 1.955a.5.5 0 0 1-.353.146H5v1.5a.5.5 0 0 1-.5.5h-2a.5.5 0 0 1-.5-.5v-2.293a.5.5 0 0 1 .146-.353l3.955-3.955A4 4 0 1 1 14 6Zm-4-2a.75.75 0 0 0 0 1.5.5.5 0 0 1 .5.5.75.75 0 0 0 1.5 0 2 2 0 0 0-2-2Z" clipRule="evenodd" /></svg>
                                <input required type="password" className="input-field" placeholder="Confirm password" onChange={(e) => { setPasswordConfirm(e.target.value) }} />
                            </label>
                        </div>
                        <div className="card-actions">
                            <input type="submit" className="submit-btn" value="Register" />
                        </div>
                        <div className="card-actions">
                            <Link className="text-neutral-500 text-md" to="/login">Login</Link>
                        </div>
                    </form>
                    <p className="error-text">{errorText}</p>
                </div>
            </div>
        </div>
    );
}

export default Register;
