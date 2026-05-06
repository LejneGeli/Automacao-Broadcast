# 📦 CESS · Gerador de Broadcast

App Streamlit para geração automática de pacotes JSON para o UnniChat.

---

## 📋 Como funciona

1. Informe a data da segunda-feira da semana
2. O sistema lê a planilha "Informações Webhook" (aba "Cursos 2026")
3. Selecione cursos e fluxos desejados
4. Clique em **Gerar Pacote ZIP**
5. Baixe e importe no UnniChat

---

### 3. Configure as credenciais (Secrets)
No painel do Streamlit Cloud:
- Vá em **Settings → Secrets**
- Cole o conteúdo do seu `credentials.json` no formato abaixo:

```toml
[gcp_service_account]
type = "service_account"
project_id = "flow-automation-unnichat"
private_key_id = "..."
private_key = "-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----\n"
client_email = "gerador-broadcast@flow-automation-unnichat.iam.gserviceaccount.com"
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."
```

> 💡 Dica: Abra seu `credentials.json` e copie os campos um a um para o formato TOML acima.

---

## 🖥️ Rodar localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

Para rodar localmente com credenciais, crie o arquivo `.streamlit/secrets.toml` com o conteúdo acima.

---

