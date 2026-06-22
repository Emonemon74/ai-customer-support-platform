postgress to sqlite, remove docker

unified login/signup

## Deployment env

For Vercel frontend:

```env
VITE_API_BASE_URL=https://your-render-service.onrender.com
```

For Render backend:

```env
GROQ_API_KEY=your-groq-api-key
DATABASE_URL=your-render-database-url
SECRET_KEY=change-this-secret
BACKEND_CORS_ORIGINS=https://your-vercel-app.vercel.app
```

If you use Vercel preview deployments, add a project-specific regex on Render:

```env
BACKEND_CORS_ORIGIN_REGEX=^https://your-vercel-project-name.*\.vercel\.app$
```
