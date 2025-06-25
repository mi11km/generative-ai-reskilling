from pydantic import BaseModel
from typing import Dict, Any


class PromptTemplates(BaseModel):
    """プロンプトテンプレートの設定"""
    
    system_prompt: str = """あなたはゲーム「スゲリス・サーガ」の仕様書に詳しいアシスタントです。
与えられたコンテキスト情報を基に、ユーザーの質問に正確かつ簡潔に回答してください。

以下の点に注意してください：
1. コンテキストに含まれる情報のみを使用して回答すること
2. 推測や憶測は避け、確実な情報のみを提供すること
3. コンテキストに情報がない場合は、その旨を明確に伝えること
4. 日本語で自然な文章で回答すること"""
    
    human_prompt: str = """コンテキスト:
{context}

質問: {question}

回答:"""
    
    context_section_format: str = "【{section}】\n{content}"
    
    no_results_message: str = "申し訳ございません。お尋ねの内容に関する情報が仕様書内で見つかりませんでした。"
    
    class Config:
        """Pydantic設定"""
        frozen = True  # イミュータブルにする


class CustomPromptTemplates(PromptTemplates):
    """カスタマイズ可能なプロンプトテンプレート"""
    
    def __init__(self, **kwargs):
        """カスタム値で初期化"""
        super().__init__(**kwargs)
    
    @classmethod
    def create_custom(
        cls,
        system_prompt: str = None,
        human_prompt: str = None,
        context_section_format: str = None,
        no_results_message: str = None
    ) -> 'CustomPromptTemplates':
        """カスタムプロンプトテンプレートを作成"""
        default_templates = PromptTemplates()
        
        return cls(
            system_prompt=system_prompt or default_templates.system_prompt,
            human_prompt=human_prompt or default_templates.human_prompt,
            context_section_format=context_section_format or default_templates.context_section_format,
            no_results_message=no_results_message or default_templates.no_results_message
        )


def get_default_prompt_templates() -> PromptTemplates:
    """デフォルトのプロンプトテンプレートを取得"""
    return PromptTemplates()


def get_prompt_templates_for_game(game_name: str) -> PromptTemplates:
    """特定のゲーム用のプロンプトテンプレートを取得"""
    game_templates = {
        "スゲリス・サーガ": PromptTemplates(),
        "example_game": CustomPromptTemplates.create_custom(
            system_prompt=f"""あなたは{game_name}の専門アシスタントです。
与えられた情報に基づいて正確に回答してください。"""
        )
    }
    
    return game_templates.get(game_name, PromptTemplates())


# プロンプトテンプレートのバリデーション
def validate_prompt_template(template: str) -> bool:
    """プロンプトテンプレートの有効性を検証"""
    required_placeholders = ["{context}", "{question}"]
    
    if not template or not isinstance(template, str):
        return False
    
    # human_promptの場合は必要なプレースホルダーがあることを確認
    if any(placeholder in template for placeholder in required_placeholders):
        return all(placeholder in template for placeholder in required_placeholders)
    
    return True