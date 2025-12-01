from .config import supabase, OPENAI_API_KEY, GROQ_API_KEY
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq

def log_to_supabase(table_name: str, data: dict):
    """
    Logs data to a specified Supabase table if the supabase client is initialized.
    
    Args:
        table_name (str): The name of the table to insert data into.
        data (dict): The data to insert.
    """
    if supabase:
        try:
            response = supabase.table(table_name).insert(data).execute()
            print(f"Logged to {table_name}: {response}")
        except Exception as e:
            print(f"Failed to log to {table_name}: {e}")

def log_usage(model_name: str, usage_metadata: dict):
    """
    Logs token usage to the 'openai-tracking' table.
    
    Args:
        model_name (str): The name of the model used.
        usage_metadata (dict): The usage metadata from the LLM response.
    """
    if supabase and usage_metadata:
        input_tokens = usage_metadata.get('input_tokens', 0)
        output_tokens = usage_metadata.get('output_tokens', 0)
        data = {
            "model": model_name,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens
        }
        log_to_supabase("openai-tracking", data)


def get_model(model_name: str, model_provider: str):
    """
    Returns an instance of the specified LLM model.
    
    Args:
        model_type (str): The type of model to instantiate ('gpt-4o' or 'groq').
    
    Returns:
        An instance of ChatOpenAI or ChatGroq.
    """
    if(model_provider == 'openai'):
        if(model_name=="gpt-5"):
            return ChatOpenAI(
                model=model_name,
                reasoning={"effort": "low"},
                api_key=OPENAI_API_KEY  
            )
        else:
            return ChatOpenAI(
                model=model_name,
                api_key=OPENAI_API_KEY  
            )
    elif(model_provider == 'groq'):
        return ChatGroq(
            model=model_name,
            api_key=GROQ_API_KEY
        )
    
    else:
        raise ValueError(f"Unsupported model type: {model_name}")