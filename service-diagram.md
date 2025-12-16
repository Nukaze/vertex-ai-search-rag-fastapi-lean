```mermaid

graph TD
    %% Subgraph for Client Side
    subgraph Client_Side ["Client Side / Public Internet"]
        style Client_Side fill:#f9f9f9,stroke:#333,stroke-width:2px
        User(["👤 User"])
        Frontend["💻 Nuxt.js Frontend<br/>(Vercel / Cloud Run)"]
    end

    %% Subgraph for Google Cloud Platform
    subgraph GCP ["Google Cloud Platform (Private)"]
        style GCP fill:#e8f0fe,stroke:#4285F4,stroke-width:2px
        
        API["🚀 Cloud Run Service<br/>(FastAPI / vertex-search-api)"]
        style API fill:#4285F4,stroke:#333,stroke-width:2px,color:white

        %% Subgraph for Vertex AI Services
        subgraph Vertex_AI ["Vertex AI Platform"]
            style Vertex_AI fill:#fff3e0,stroke:#EA4335,stroke-width:2px
            Search["🔍 Vertex AI Search<br/>(Discovery Engine)"]
            style Search fill:#EA4335,stroke:#333,stroke-width:2px,color:white
            
            LLM["🧠 Gemini Pro 2.5 flash<br/>(Generative Model)"]
            style LLM fill:#FBBC04,stroke:#333,stroke-width:2px,color:white
        end
    end

    %% Data Flow Connections
    User -- "1. Question" --> Frontend
    Frontend -- "2. POST /api/vertex-search" --> API
    
    API -- "3. Search Query" --> Search
    Search -.-> |"4. Relevant Chunks"| API
    
    API -- "5. Prompt (Context + Query)" --> LLM
    LLM -.-> |"6. Answer + Citations"| API
    
    API -.-> |"7. JSON Response"| Frontend
    Frontend -.-> |"8. Rendering UI"| User