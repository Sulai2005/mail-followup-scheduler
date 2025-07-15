def fill_prompt_template(prompt, analysis):
    try:
        return prompt.format(**analysis)
    except Exception:
        return prompt 