def retriever_format_docs(docs):
    return "\n".join(format_doc(doc.page_content, doc.metadata) for doc in docs)

def format_doc(page_content, metadata, full_content=True):
    formatted_doc = ""
    formatted_doc += format_metadata(metadata)
    if metadata['type'] == 'email':
        formatted_doc += format_email_doc(page_content, metadata, full_content)
    elif metadata['source'] == 'gdrive':
        formatted_doc += format_gdrive_doc(page_content, metadata, full_content)
    else:
        assert(False)
    return formatted_doc

def format_gdrive_doc(page_content, metadata, full_content=True):
    formatted_doc = ""
    formatted_doc += "GDrive Document Details\n"
    formatted_doc += "----------------------\n"
    formatted_doc += f"File ID: {metadata.get('gdrive_file_id', 'N/A')}\n"
    formatted_doc += f"Name: {metadata.get('name', 'N/A')}\n"
    formatted_doc += f"Mime Type: {metadata.get('mime_type', 'N/A')}\n"
    formatted_doc += f"Owners: {metadata.get('owners', 'N/A')}\n"
    formatted_doc += f"Created Time: {metadata.get('created_time', 'N/A')}\n"
    formatted_doc += f"Modified Time: {metadata.get('modified_time', 'N/A')}\n"
    formatted_doc += "\nContent:\n"
    formatted_doc += "----------------------\n"
    if full_content:
        formatted_doc += page_content
    else:
        formatted_doc += page_content[:50] + "..."
    return formatted_doc

def format_email_doc(page_content, metadata, full_content=True):
    formatted_doc = ""
    formatted_doc += "Email Document Details\n"
    formatted_doc += "----------------------\n"
    formatted_doc += f"Email ID: {metadata.get('email_id', 'N/A')}\n"
    formatted_doc += f"Thread ID: {metadata.get('thread_id', 'N/A')}\n"
    formatted_doc += f"Subject: {metadata.get('subject', 'N/A')}\n"
    formatted_doc += f"From: {metadata.get('from_address', 'N/A')}\n"
    formatted_doc += f"To: {metadata.get('to_address', 'N/A')}\n"
    formatted_doc += "\nContent:\n"
    formatted_doc += "----------------------\n"
    if full_content:
        formatted_doc += page_content
    else:
        formatted_doc += page_content[:50] + "..."
    return formatted_doc

def format_metadata(metadata):
    formatted_metadata = str(metadata) + "\n"
    return formatted_metadata