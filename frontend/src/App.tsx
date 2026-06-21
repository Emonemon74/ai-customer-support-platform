import { Toaster } from "react-hot-toast";

import { AppRoutes } from "./routes/AppRoutes";

function App() {
  return (
    <>
      <AppRoutes />

      <Toaster
        position="top-right"
        reverseOrder={false}
        gutter={12}
        toastOptions={{
          duration: 3000,
          style: {
            background: "#0f172a",
            color: "#ffffff",
            borderRadius: "12px",
            padding: "14px 16px",
            fontSize: "14px",
          },
          success: {
            iconTheme: {
              primary: "#22c55e",
              secondary: "#ffffff",
            },
          },
          error: {
            iconTheme: {
              primary: "#ef4444",
              secondary: "#ffffff",
            },
          },
        }}
      />
    </>
  );
}

export default App;