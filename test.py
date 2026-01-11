from openai import OpenAI

client = OpenAI()


def ask_gpt():
    prompt = f"Give me Sajde song youtube link"
    response = client.responses.create(
                      model="gpt-4.1-nano",
                      input= prompt ,
                      store=False,)
      
    print(response.output_text)
ask_gpt()