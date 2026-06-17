import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { LoginForm } from '@/features/auth/components/LoginForm';
import authReducer from '@/features/auth/store/authSlice';

const store = configureStore({ reducer: { auth: authReducer } });

describe('LoginForm', () => {
  it('renders login form', () => {
    render(
      <Provider store={store}>
        <BrowserRouter>
          <LoginForm />
        </BrowserRouter>
      </Provider>,
    );
    expect(screen.getByText('IPE Login')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('admin@demo.com')).toBeInTheDocument();
  });
});
