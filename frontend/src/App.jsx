import { RouterProvider } from "react-router-dom";
import { router } from "./routes/routes.jsx";

function App() {
  return (
    <>
      <RouterProvider router={router}>
        <h1>Hello Vhio</h1>
      </RouterProvider>
    </>
  );
}

export default App;
