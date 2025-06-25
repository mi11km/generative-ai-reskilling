import pytest
from pydantic import ValidationError

from src.config.prompts import (
    PromptTemplates,
    CustomPromptTemplates,
    get_default_prompt_templates,
    get_prompt_templates_for_game,
    validate_prompt_template,
)


class TestPromptTemplates:
    """PromptTemplates クラスのテスト"""

    def test_default_prompt_templates(self):
        """デフォルトのプロンプトテンプレートをテスト"""
        templates = PromptTemplates()

        # 必須フィールドが設定されていることを確認
        assert templates.system_prompt is not None
        assert templates.human_prompt is not None
        assert templates.context_section_format is not None
        assert templates.no_results_message is not None

        # デフォルト値の内容確認
        assert "スゲリス・サーガ" in templates.system_prompt
        assert "アシスタント" in templates.system_prompt
        assert "{context}" in templates.human_prompt
        assert "{question}" in templates.human_prompt
        assert "【{section}】" in templates.context_section_format
        assert "{content}" in templates.context_section_format
        assert "見つかりませんでした" in templates.no_results_message

    def test_prompt_templates_immutable(self):
        """プロンプトテンプレートがイミュータブルであることをテスト"""
        templates = PromptTemplates()

        # フィールドを変更しようとすると例外が発生することを確認
        with pytest.raises(ValidationError):
            templates.system_prompt = "新しいシステムプロンプト"

    def test_prompt_templates_with_custom_values(self):
        """カスタム値でのプロンプトテンプレート作成をテスト"""
        custom_system_prompt = "カスタムシステムプロンプトです。"
        custom_human_prompt = "質問: {question}\nコンテキスト: {context}\n回答:"

        templates = PromptTemplates(
            system_prompt=custom_system_prompt, human_prompt=custom_human_prompt
        )

        assert templates.system_prompt == custom_system_prompt
        assert templates.human_prompt == custom_human_prompt
        # デフォルト値は保持される
        assert "【{section}】" in templates.context_section_format

    def test_prompt_templates_validation(self):
        """プロンプトテンプレートのバリデーションをテスト"""
        # 空の文字列でも作成可能（バリデーションは別関数で行う）
        templates = PromptTemplates(system_prompt="", human_prompt="")

        assert templates.system_prompt == ""
        assert templates.human_prompt == ""


class TestCustomPromptTemplates:
    """CustomPromptTemplates クラスのテスト"""

    def test_create_custom_with_all_parameters(self):
        """すべてのパラメータでカスタムテンプレート作成をテスト"""
        custom_templates = CustomPromptTemplates.create_custom(
            system_prompt="カスタムシステム",
            human_prompt="カスタムヒューマン: {question} | {context}",
            context_section_format="[{section}] {content}",
            no_results_message="カスタム結果なしメッセージ",
        )

        assert custom_templates.system_prompt == "カスタムシステム"
        assert (
            custom_templates.human_prompt
            == "カスタムヒューマン: {question} | {context}"
        )
        assert custom_templates.context_section_format == "[{section}] {content}"
        assert custom_templates.no_results_message == "カスタム結果なしメッセージ"

    def test_create_custom_with_partial_parameters(self):
        """一部のパラメータのみでカスタムテンプレート作成をテスト"""
        custom_templates = CustomPromptTemplates.create_custom(
            system_prompt="部分的カスタムシステム"
        )

        # カスタム値が設定される
        assert custom_templates.system_prompt == "部分的カスタムシステム"

        # その他はデフォルト値が使用される
        default_templates = PromptTemplates()
        assert custom_templates.human_prompt == default_templates.human_prompt
        assert (
            custom_templates.context_section_format
            == default_templates.context_section_format
        )
        assert (
            custom_templates.no_results_message == default_templates.no_results_message
        )

    def test_create_custom_with_no_parameters(self):
        """パラメータなしでカスタムテンプレート作成をテスト"""
        custom_templates = CustomPromptTemplates.create_custom()
        default_templates = PromptTemplates()

        # すべてデフォルト値と同じになる
        assert custom_templates.system_prompt == default_templates.system_prompt
        assert custom_templates.human_prompt == default_templates.human_prompt
        assert (
            custom_templates.context_section_format
            == default_templates.context_section_format
        )
        assert (
            custom_templates.no_results_message == default_templates.no_results_message
        )


class TestPromptTemplateFunctions:
    """プロンプトテンプレート関数のテスト"""

    def test_get_default_prompt_templates(self):
        """get_default_prompt_templates 関数のテスト"""
        templates = get_default_prompt_templates()

        assert isinstance(templates, PromptTemplates)
        assert "スゲリス・サーガ" in templates.system_prompt

    def test_get_prompt_templates_for_game_known_game(self):
        """既知のゲーム名でのプロンプトテンプレート取得をテスト"""
        templates = get_prompt_templates_for_game("スゲリス・サーガ")

        assert isinstance(templates, PromptTemplates)
        assert "スゲリス・サーガ" in templates.system_prompt

    def test_get_prompt_templates_for_game_unknown_game(self):
        """未知のゲーム名でのプロンプトテンプレート取得をテスト"""
        templates = get_prompt_templates_for_game("未知のゲーム")

        # デフォルトテンプレートが返される
        assert isinstance(templates, PromptTemplates)
        default_templates = PromptTemplates()
        assert templates.system_prompt == default_templates.system_prompt

    def test_get_prompt_templates_for_game_example_game(self):
        """example_game でのプロンプトテンプレート取得をテスト"""
        templates = get_prompt_templates_for_game("example_game")

        assert isinstance(templates, CustomPromptTemplates)
        assert "example_game" in templates.system_prompt


class TestPromptTemplateValidation:
    """プロンプトテンプレートバリデーションのテスト"""

    def test_validate_prompt_template_valid_human_prompt(self):
        """有効なhuman_promptのバリデーションをテスト"""
        valid_template = "質問: {question}\nコンテキスト: {context}\n回答:"

        assert validate_prompt_template(valid_template) is True

    def test_validate_prompt_template_valid_system_prompt(self):
        """有効なsystem_promptのバリデーションをテスト"""
        valid_template = "あなたは専門アシスタントです。"

        assert validate_prompt_template(valid_template) is True

    def test_validate_prompt_template_missing_placeholders(self):
        """プレースホルダーが不足しているテンプレートのバリデーションをテスト"""
        # {context}のみ（{question}が不足）
        invalid_template = "コンテキスト: {context}"

        assert validate_prompt_template(invalid_template) is False

        # {question}のみ（{context}が不足）
        invalid_template = "質問: {question}"

        assert validate_prompt_template(invalid_template) is False

    def test_validate_prompt_template_empty_or_none(self):
        """空またはNoneのテンプレートのバリデーションをテスト"""
        assert validate_prompt_template("") is False
        assert validate_prompt_template(None) is False
        assert validate_prompt_template(123) is False

    def test_validate_prompt_template_no_placeholders(self):
        """プレースホルダーがないテンプレートのバリデーションをテスト"""
        # プレースホルダーがない場合は有効とする（システムプロンプトなど）
        valid_template = "あなたは専門的なアシスタントです。"

        assert validate_prompt_template(valid_template) is True


class TestPromptTemplateIntegration:
    """プロンプトテンプレートの統合テスト"""

    def test_template_string_formatting(self):
        """テンプレート文字列のフォーマッティングをテスト"""
        templates = PromptTemplates()

        # human_promptのフォーマッティング
        formatted_human = templates.human_prompt.format(
            context="テストコンテキスト", question="テスト質問"
        )

        assert "テストコンテキスト" in formatted_human
        assert "テスト質問" in formatted_human

        # context_section_formatのフォーマッティング
        formatted_section = templates.context_section_format.format(
            section="テストセクション", content="テストコンテンツ"
        )

        assert "【テストセクション】" in formatted_section
        assert "テストコンテンツ" in formatted_section

    def test_templates_with_japanese_content(self):
        """日本語コンテンツでのテンプレート動作をテスト"""
        templates = PromptTemplates()

        japanese_context = "ゲームの基本システムについて説明します。"
        japanese_question = "バトルシステムはどのようになっていますか？"

        formatted = templates.human_prompt.format(
            context=japanese_context, question=japanese_question
        )

        assert japanese_context in formatted
        assert japanese_question in formatted
        assert "コンテキスト:" in formatted
        assert "質問:" in formatted

    def test_templates_with_special_characters(self):
        """特殊文字を含むコンテンツでのテンプレート動作をテスト"""
        templates = PromptTemplates()

        special_content = "特殊文字: !@#$%^&*()_+-=[]{}|;':\",./<>?"

        formatted_section = templates.context_section_format.format(
            section="特殊文字テスト", content=special_content
        )

        assert special_content in formatted_section
        assert "【特殊文字テスト】" in formatted_section


@pytest.mark.parametrize(
    "game_name,expected_type",
    [
        ("スゲリス・サーガ", PromptTemplates),
        ("example_game", CustomPromptTemplates),
        ("unknown_game", PromptTemplates),
        ("", PromptTemplates),
    ],
)
def test_get_prompt_templates_for_game_parametrized(game_name, expected_type):
    """様々なゲーム名でのプロンプトテンプレート取得をパラメータ化テストで検証"""
    templates = get_prompt_templates_for_game(game_name)
    assert isinstance(templates, expected_type)


@pytest.mark.parametrize(
    "template,expected_valid",
    [
        ("質問: {question}\nコンテキスト: {context}", True),
        ("{context} から {question} に答えて", True),
        ("システムプロンプトです", True),
        ("質問: {question}", False),
        ("コンテキスト: {context}", False),
        ("", False),
        (None, False),
    ],
)
def test_validate_prompt_template_parametrized(template, expected_valid):
    """様々なテンプレートのバリデーションをパラメータ化テストで検証"""
    result = validate_prompt_template(template)
    assert result == expected_valid
