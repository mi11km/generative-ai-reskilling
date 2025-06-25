import type { MetaFunction } from "@remix-run/node";
import { ChatInterface } from "../components/ChatInterface";

export const meta: MetaFunction = () => {
  return [
    { title: "ゲーム仕様問い合わせBOT" },
    { name: "description", content: "ゲーム仕様について質問できるAIチャットボット" },
  ];
};

export default function Index() {
  return <ChatInterface />;
}
