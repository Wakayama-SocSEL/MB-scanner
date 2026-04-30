# equivalence-checker

`(setup, slow, fast)` トリプルを sandbox 実行し、出力を 4 つの直交軸 (oracle) で観測して **`equal` / `not_equal` / `error`** verdict を返す。`checker.checkEquivalence()` が公開エントリポイント。

## ファイル index

```
src/equivalence-checker/
├── checker.ts    ← 公開 checkEquivalence。slow/fast 双方の sandbox 実行 + 4 oracle 集約
├── verdict.ts    ← deriveOverallVerdict (4 oracle 観測の合成優先順位ロジック)
├── index.ts      ← 公開 re-export
├── oracles/
│   ├── return-value.ts        ← 戻り値の文字列正規化比較
│   ├── argument-mutation.ts   ← 引数の pre/post スナップショット差分 (in-place 破壊検出)
│   ├── exception.ts           ← 例外型 + メッセージ比較
│   └── external-observation.ts ← console 呼出列 + 新規 global 変数の正規化比較
└── sandbox/
    ├── executor.ts    ← vm.Script ベースの隔離実行。timeout / setup / body の分離
    ├── serializer.ts  ← 値 → 正規化文字列 (NaN / Map / Set / 循環 等の扱い)
    └── stabilizer.ts  ← vm context 構築 + 非決定性 API の遮断・固定化・console hook
```

## 依存方向

```
checker.ts ─ verdict.ts ─ shared/types
 ├─ oracles/return-value     ─┐
 ├─ oracles/argument-mutation ┤
 ├─ oracles/exception         ├─ sandbox/executor ─ sandbox/serializer
 ├─ oracles/external-obs.     ┘                   ─ sandbox/stabilizer
```

葉ノードは `sandbox/serializer.ts` (依存なし) と `sandbox/stabilizer.ts` (`node:vm` のみ)。oracles 層は sandbox 層にのみ依存し、oracle 同士は独立。
