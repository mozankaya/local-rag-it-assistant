import { useState } from "react";
import type { SyntheticEvent } from "react";
import {
  getCurrentUser,
  loginUser,
  saveAccessToken,
  type CurrentUserResponse,
} from "../api/authApi";

type LoginPageProps = {
  onLoginSuccess: (user: CurrentUserResponse) => void;
};

function LoginPage({ onLoginSuccess }: LoginPageProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  async function handleSubmit(event: SyntheticEvent<HTMLFormElement>) {
    event.preventDefault();

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
      <section className="login-card">
        <div className="login-brand">IZELTAS</div>

        <div className="login-icon">IT</div>

        <h1>İZELTAŞ IT Danışma Asistanı</h1>
        <p>
          Lokal LLM ve RAG destekli IT yardım sistemine erişmek için giriş
          yapın.
        </p>

        <form className="login-form" onSubmit={handleSubmit}>
          <label>
            E-posta
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="E-posta adresinizi girin"
              autoComplete="email"
            />
          </label>

          <label>
            Şifre
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Şifrenizi girin"
              autoComplete="current-password"
            />
          </label>

          {errorMessage && <div className="login-error">{errorMessage}</div>}

          <button type="submit" disabled={isLoading}>
            {isLoading ? "Giriş yapılıyor..." : "Giriş Yap"}
          </button>
        </form>

        <div className="login-helper">
          <span>Demo kullanıcılar:</span>
          <small>admin@izeltas.local / Admin123!</small>
          <small>user@izeltas.local / User123!</small>
        </div>
      </section>
    </main>
  );
}

export default LoginPage;
