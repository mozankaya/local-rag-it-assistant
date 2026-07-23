import { useState } from "react";
import type { FormEvent } from "react";
import {
  AdminUsersApiError,
  createUser,
  type UserRole,
} from "../../api/adminUsersApi";

interface UserCreateFormProps {
  onCreated: () => void;
  onUnauthorized: () => void;
  onForbidden: () => void;
}

function UserCreateForm({
  onCreated,
  onUnauthorized,
  onForbidden,
}: UserCreateFormProps) {
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<UserRole>("user");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("");
    setError("");
    setIsSubmitting(true);

    try {
      await createUser({
        full_name: fullName.trim(),
        email: email.trim(),
        password,
        role,
      });

      setFullName("");
      setEmail("");
      setPassword("");
      setRole("user");
      setMessage("Kullanıcı başarıyla oluşturuldu.");
      onCreated();
    } catch (requestError) {
      if (requestError instanceof AdminUsersApiError) {
        if (requestError.status === 401) {
          onUnauthorized();
          return;
        }
        if (requestError.status === 403) {
          onForbidden();
          return;
        }
        if (requestError.status === 409) {
          setError("Bu e-posta adresiyle kayıtlı bir kullanıcı zaten var.");
          return;
        }
      }

      setError("Kullanıcı oluşturulamadı. Bilgileri kontrol edip tekrar deneyin.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <article className="admin-panel user-create-panel">
      <div className="admin-panel-header">
        <div>
          <h2>Yeni kullanıcı</h2>
          <p>Sisteme erişecek yeni kullanıcı hesabı oluşturun</p>
        </div>
      </div>

      <form className="user-create-form" onSubmit={handleSubmit}>
        <label>
          Ad soyad
          <input
            type="text"
            value={fullName}
            onChange={(event) => setFullName(event.target.value)}
            minLength={2}
            maxLength={100}
            required
          />
        </label>

        <label>
          E-posta
          <input
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
        </label>

        <label>
          Şifre
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            minLength={6}
            maxLength={72}
            autoComplete="new-password"
            required
          />
        </label>

        <label>
          Rol
          <select value={role} onChange={(event) => setRole(event.target.value as UserRole)}>
            <option value="user">Kullanıcı</option>
            <option value="admin">Admin</option>
          </select>
        </label>

        <button type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Oluşturuluyor..." : "Kullanıcı oluştur"}
        </button>
      </form>

      {message && <div className="admin-success" role="status">{message}</div>}
      {error && <div className="admin-form-error" role="alert">{error}</div>}
    </article>
  );
}

export default UserCreateForm;
