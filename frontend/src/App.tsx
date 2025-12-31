import { BrowserRouter, Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import SpacesPage from "./pages/SpacesPage";
import SpaceDetailPage from "./pages/SpaceDetailPage";
import RunsPage from "./pages/RunsPage";
import ItemsPage from "./pages/ItemsPage";
import ItemDetailPage from "./pages/ItemDetailPage";
import ConfigPage from "./pages/ConfigPage";
import IngestPage from "./pages/IngestPage";
import LLMConfigPage from "./pages/LLMConfigPage";
import PromptEditorPage from "./pages/PromptEditorPage";
import GlobalConfigPage from "./pages/GlobalConfigPage";
import SystemPage from "./pages/SystemPage";

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<SpacesPage />} />
          <Route path="/spaces/:spaceId" element={<SpaceDetailPage />} />
          <Route path="/spaces/:spaceId/runs" element={<RunsPage />} />
          <Route path="/spaces/:spaceId/items" element={<ItemsPage />} />
          <Route path="/spaces/:spaceId/items/:itemId" element={<ItemDetailPage />} />
          <Route path="/spaces/:spaceId/config" element={<ConfigPage />} />
          <Route path="/spaces/:spaceId/ingest" element={<IngestPage />} />
          <Route path="/config/global" element={<GlobalConfigPage />} />
          <Route path="/config/llm" element={<LLMConfigPage />} />
          <Route path="/config/prompts" element={<PromptEditorPage />} />
          <Route path="/system" element={<SystemPage />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;

