import { useState } from "react";
import type { SyntheticEvent } from "react";
import {
  getCurrentUser,
  loginUser,
  saveAccessToken,
  type CurrentUserResponse,
} from "../../api/authApi";
import izeltasLogo from "../../assets/izeltas-logo.png";
import "./LoginPage.css";

type LoginPageProps = {
  onLoginSuccess: (user: CurrentUserResponse) => void;
};

function LoginPage({ onLoginSuccess }: LoginPageProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isPasswordVisible, setIsPasswordVisible] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  async function handleSubmit(event: SyntheticEvent<HTMLFormElement>) {
    event.preventDefault();
    if (isLoading) return;

    setErrorMessage("");
    setIsLoading(true);

    try {
      const tokenResponse = await loginUser({
        email,
        password,
      });

      saveAccessToken(tokenResponse.access_token);

      const user = await getCurrentUser();

      onLoginSuccess(user);
    } catch {
      setErrorMessage("E-posta veya şifre hatalı. Lütfen tekrar deneyin.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="login-page">
      <div className="login-shell">
        <header className="login-brand">
          <img className="login-logo" src={izeltasLogo} alt="İzeltaş" />
          <div className="login-product-label">IT DANIŞMA ASİSTANI</div>
        </header>

        <section className="login-card" aria-labelledby="login-title">
          <div className="login-heading-area">
            <h1 id="login-title">Hesabınızla giriş yapın</h1>
            <p>IT süreçleri için yerel ve güvenli destek.</p>
          </div>

          <form
            className="login-form"
            onSubmit={handleSubmit}
            aria-busy={isLoading}
          >
            <label htmlFor="login-email">
              E-posta
              <input
                id="login-email"
                name="email"
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="E-posta adresinizi girin"
                autoComplete="username"
                aria-describedby={errorMessage ? "login-error-message" : undefined}
              />
            </label>

            <div className="login-password-field">
              <label htmlFor="login-password">Şifre</label>
              <div className="login-password-input">
                <input
                  id="login-password"
                  name="password"
                  type={isPasswordVisible ? "text" : "password"}
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder="Şifrenizi girin"
                  autoComplete="current-password"
                  aria-describedby={errorMessage ? "login-error-message" : undefined}
                />
                <button
                  className="login-password-toggle"
                  type="button"
                  onClick={() => setIsPasswordVisible((current) => !current)}
                  aria-label={isPasswordVisible ? "Şifreyi gizle" : "Şifreyi göster"}
                >
                  {isPasswordVisible ? "Gizle" : "Göster"}
                </button>
              </div>
            </div>

            {errorMessage && (
              <div id="login-error-message" className="login-error" role="alert">
                {errorMessage}
              </div>
            )}

            <button
              className="login-submit"
              type="submit"
              disabled={isLoading}
              aria-busy={isLoading}
            >
              {isLoading ? "Giriş yapılıyor..." : "Giriş Yap"}
            </button>
          </form>

          <p className="login-security-note">
            Tüm işlemler yerel sistem üzerinde gerçekleştirilir.
          </p>
        </section>
      </div>
    </main>
  );
}

export default LoginPage;
