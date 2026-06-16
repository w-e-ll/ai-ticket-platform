from __future__ import annotations

import json
from uuid import UUID

import requests
import streamlit as st


API_BASE_URL = "http://localhost:8000/api/v1"


st.set_page_config(
    page_title="AI Ticket Platform",
    page_icon="🎫",
    layout="wide",
)


def api_request(
    *,
    method: str,
    endpoint: str,
    json_payload: dict | None = None,
    files: dict | None = None,
    params: dict | None = None,
) -> dict:
    """Execute API request."""
    url = f"{API_BASE_URL}{endpoint}"

    try:
        response = requests.request(
            method=method,
            url=url,
            json=json_payload,
            files=files,
            params=params,
            timeout=120,
        )

        response.raise_for_status()

        return response.json()

    except requests.HTTPError as exc:
        st.error(f"HTTP error: {exc}")

        try:
            st.json(response.json())
        except Exception:
            st.text(response.text)

        return {}

    except Exception as exc:
        st.error(f"Request failed: {exc}")
        return {}


st.title("🎫 AI Ticket Platform")
st.caption("Enterprise AI SaaS for ticket routing and RAG support")


tab_chat, tab_ticket, tab_documents, tab_admin = st.tabs(
    [
        "💬 AI Chat",
        "🎫 Tickets",
        "📄 Documents",
        "⚙️ Admin",
    ]
)


with tab_chat:
    st.header("AI Knowledge Base Chat")

    tenant_id_chat = st.text_input(
        "Tenant ID",
        key="chat_tenant_id",
    )

    department_chat = st.text_input(
        "Department Filter (optional)",
        key="chat_department",
    )

    top_k = st.slider(
        "Top K Results",
        min_value=1,
        max_value=20,
        value=5,
    )

    chat_question = st.text_area(
        "Ask a Question",
        height=180,
        placeholder="How do I reset VPN access?",
    )

    if st.button("Ask AI", type="primary"):
        if not tenant_id_chat.strip():
            st.error("Tenant ID is required")

        elif not chat_question.strip():
            st.error("Question is required")

        else:
            with st.spinner("Generating answer..."):
                response = api_request(
                    method="POST",
                    endpoint="/chat/ask",
                    json_payload={
                        "tenant_id": tenant_id_chat,
                        "message": chat_question,
                        "top_k": top_k,
                    },
                    params={
                        "department": department_chat or None,
                    },
                )

            if response:
                st.subheader("AI Answer")
                st.write(response.get("answer"))

                contexts = response.get("contexts", [])

                if contexts:
                    st.subheader("Retrieved Contexts")

                    for index, context in enumerate(contexts, start=1):
                        with st.expander(
                            f"Context #{index} | Score: {context.get('score', 0):.4f}"
                        ):
                            st.write(context.get("content"))

                            metadata = context.get("metadata", {})

                            if metadata:
                                st.json(metadata)


with tab_ticket:
    st.header("Create Support Ticket")

    tenant_id_ticket = st.text_input(
        "Tenant ID",
        key="ticket_tenant_id",
    )

    created_by_user_id = st.text_input(
        "Created By User ID (optional)",
        key="created_by_user_id",
    )

    ticket_title = st.text_input(
        "Ticket Title",
        placeholder="VPN access issue",
    )

    ticket_description = st.text_area(
        "Ticket Description",
        height=250,
        placeholder="Describe the issue...",
    )

    ticket_priority = st.selectbox(
        "Priority",
        options=["low", "medium", "high", "critical"],
        index=1,
    )

    ticket_department = st.selectbox(
        "Department",
        options=[
            "",
            "hr",
            "it",
            "transportation",
            "finance",
            "legal",
            "security",
        ],
    )

    if st.button("Create Ticket", type="primary"):
        if not tenant_id_ticket.strip():
            st.error("Tenant ID is required")

        elif not ticket_title.strip():
            st.error("Ticket title is required")

        elif not ticket_description.strip():
            st.error("Ticket description is required")

        else:
            payload = {
                "tenant_id": tenant_id_ticket,
                "created_by_user_id": (
                    created_by_user_id or None
                ),
                "title": ticket_title,
                "description": ticket_description,
                "priority": ticket_priority,
                "department": (
                    ticket_department or None
                ),
            }

            with st.spinner("Creating ticket..."):
                response = api_request(
                    method="POST",
                    endpoint="/tickets",
                    json_payload=payload,
                )

            if response:
                st.success("Ticket created successfully")
                st.json(response)


with tab_documents:
    st.header("Upload Knowledge Base Documents")

    tenant_id_document = st.text_input(
        "Tenant ID",
        key="document_tenant_id",
    )

    document_department = st.selectbox(
        "Department",
        options=[
            "",
            "hr",
            "it",
            "transportation",
            "finance",
            "legal",
            "security",
        ],
        key="document_department",
    )

    uploaded_file = st.file_uploader(
        "Upload Document",
        type=["pdf", "docx", "txt"],
    )

    if st.button("Upload Document", type="primary"):
        if not tenant_id_document.strip():
            st.error("Tenant ID is required")

        elif uploaded_file is None:
            st.error("Document file is required")

        else:
            with st.spinner("Uploading and indexing document..."):
                response = api_request(
                    method="POST",
                    endpoint="/documents/upload",
                    params={
                        "tenant_id": tenant_id_document,
                        "department": (
                            document_department or None
                        ),
                    },
                    files={
                        "file": (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            uploaded_file.type,
                        )
                    },
                )

            if response:
                st.success("Document uploaded and indexed")
                st.json(response)


with tab_admin:
    st.header("Admin Tools")

    admin_action = st.selectbox(
        "Action",
        options=[
            "Classify Ticket Text",
            "List Tickets",
            "List Documents",
        ],
    )

    if admin_action == "Classify Ticket Text":
        admin_text = st.text_area(
            "Ticket Text",
            height=220,
            placeholder="Paste raw ticket text...",
        )

        if st.button("Run Classification"):
            if not admin_text.strip():
                st.error("Text is required")

            else:
                with st.spinner("Classifying..."):
                    response = api_request(
                        method="POST",
                        endpoint="/admin/classify",
                        params={
                            "text": admin_text,
                        },
                    )

                if response:
                    st.success("Classification completed")
                    st.json(response)

    elif admin_action == "List Tickets":
        tenant_id_admin_tickets = st.text_input(
            "Tenant ID",
            key="tenant_id_admin_tickets",
        )

        if st.button("Load Tickets"):
            if not tenant_id_admin_tickets.strip():
                st.error("Tenant ID is required")

            else:
                with st.spinner("Loading tickets..."):
                    response = api_request(
                        method="GET",
                        endpoint="/tickets",
                        params={
                            "tenant_id": tenant_id_admin_tickets,
                        },
                    )

                if response:
                    st.subheader("Tickets")
                    st.json(response)

    elif admin_action == "List Documents":
        tenant_id_admin_documents = st.text_input(
            "Tenant ID",
            key="tenant_id_admin_documents",
        )

        if st.button("Load Documents"):
            if not tenant_id_admin_documents.strip():
                st.error("Tenant ID is required")

            else:
                with st.spinner("Loading documents..."):
                    response = api_request(
                        method="GET",
                        endpoint="/documents",
                        params={
                            "tenant_id": tenant_id_admin_documents,
                        },
                    )

                if response:
                    st.subheader("Documents")
                    st.json(response)


with st.sidebar:
    st.header("Platform Information")

    st.markdown(
        """
        ### Features

        - AI ticket routing
        - RAG knowledge base search
        - Enterprise document indexing
        - Ticket summarization
        - Escalation analysis
        - Multi-tenant architecture
        - Vector search
        - Streamlit admin panel
        """
    )

    st.divider()

    st.subheader("API")

    st.code(API_BASE_URL)

    if st.button("Check API Health"):
        response = api_request(
            method="GET",
            endpoint="/health",
        )

        if response:
            st.success("API is healthy")
            st.json(response)

    st.divider()

    st.subheader("Example Tenant ID")

    sample_tenant_id = "11111111-1111-1111-1111-111111111111"

    st.code(sample_tenant_id)

    st.divider()

    st.subheader("Debug")

    if st.checkbox("Show Session State"):
        st.json(
            {
                key: str(value)
                for key, value in st.session_state.items()
            }
        )
