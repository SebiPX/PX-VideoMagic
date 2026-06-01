import React, { createContext, useContext, useEffect, useState } from 'react';

const AuthContext = createContext(undefined);

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};

const API_BASE_URL = 'https://api.labs-schickeria.com';

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const token = localStorage.getItem('labs_token');
        if (!token) {
            setLoading(false);
            return;
        }

        fetch(`${API_BASE_URL}/auth/me`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        })
        .then(res => {
            if (!res.ok) throw new Error("Invalid token");
            return res.json();
        })
        .then(userData => {
            setUser(userData);
        })
        .catch(() => {
            localStorage.removeItem('labs_token');
        })
        .finally(() => setLoading(false));
    }, []);

    const signIn = async (email, password) => {
        try {
            const res = await fetch(`${API_BASE_URL}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });
            const data = await res.json();
            
            if (!res.ok) throw new Error(data.error || 'Login failed');
            
            localStorage.setItem('labs_token', data.token);
            setUser(data.user);
            return { error: null };
        } catch (err) {
            return { error: err };
        }
    };

    const signOut = async () => {
        localStorage.removeItem('labs_token');
        setUser(null);
    };

    const value = {
        user,
        loading,
        signIn,
        signOut
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
