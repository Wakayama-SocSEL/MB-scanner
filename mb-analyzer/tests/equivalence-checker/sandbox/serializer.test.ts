import { describe, expect, it } from "vitest";
import {
  SerializationError,
  serializeNumber,
  serializeValue,
} from "../../../src/equivalence-checker/sandbox/serializer";

describe("serializeNumber", () => {
  it("NaN / Infinity / -Infinity / -0 を区別する", () => {
    expect(serializeNumber(NaN)).toBe("NaN");
    expect(serializeNumber(Infinity)).toBe("Infinity");
    expect(serializeNumber(-Infinity)).toBe("-Infinity");
    expect(serializeNumber(-0)).toBe("-0");
    expect(serializeNumber(0)).toBe("0");
    expect(serializeNumber(3.14)).toBe("3.14");
  });
});

describe("serializeValue: primitives", () => {
  it("undefined / null / boolean", () => {
    expect(serializeValue(undefined)).toBe("undefined");
    expect(serializeValue(null)).toBe("null");
    expect(serializeValue(true)).toBe("true");
    expect(serializeValue(false)).toBe("false");
  });

  it("string は JSON エスケープされる", () => {
    expect(serializeValue("a\"b")).toBe('"a\\"b"');
    expect(serializeValue("")).toBe('""');
  });

  it("bigint は suffix n 付き", () => {
    expect(serializeValue(BigInt(42))).toBe("42n");
    expect(serializeValue(BigInt("100000000000000000000"))).toBe("100000000000000000000n");
  });

  it("symbol / 関数は専用トークン", () => {
    expect(serializeValue(Symbol("foo"))).toBe("<symbol:foo>");
    expect(serializeValue(Symbol())).toBe("<symbol:>");
    expect(serializeValue(() => 1)).toBe("<function>");
  });
});

describe("serializeValue: objects / arrays", () => {
  it("配列は要素をコンマ区切りで連結", () => {
    expect(serializeValue([1, "a", true, null])).toBe('[1,"a",true,null]');
  });

  it("オブジェクトのキーは sort 済みで順序非依存", () => {
    const a = serializeValue({ b: 1, a: 2 });
    const b = serializeValue({ a: 2, b: 1 });
    expect(a).toBe(b);
    expect(a).toBe('{"a":2,"b":1}');
  });

  it("ネストしたオブジェクトも再帰的に展開される", () => {
    const s = serializeValue({ x: [1, { y: 2 }] });
    expect(s).toBe('{"x":[1,{"y":2}]}');
  });

  it("Date / Map / Set はクラス名付きの表現", () => {
    expect(serializeValue(new Date(0))).toBe("<Date:0>");
    expect(serializeValue(new Map([["a", 1]]))).toBe('<Map:{"a"=>1}>');
    expect(serializeValue(new Set([1, 2]))).toBe("<Set:{1,2}>");
  });

  it("NaN / -0 を含む配列・オブジェクトも区別", () => {
    expect(serializeValue([NaN, -0])).toBe("[NaN,-0]");
    expect(serializeValue({ x: NaN })).toBe('{"x":NaN}');
  });
});

describe("serializeValue: circular reference", () => {
  it("自己参照配列は SerializationError", () => {
    const arr: unknown[] = [];
    arr.push(arr);
    expect(() => serializeValue(arr)).toThrow(SerializationError);
  });

  it("相互参照オブジェクトは SerializationError", () => {
    const a: Record<string, unknown> = {};
    const b: Record<string, unknown> = { a };
    a.b = b;
    expect(() => serializeValue(a)).toThrow(SerializationError);
  });

  it("同じサブツリーを 2 箇所に埋め込むのは循環ではない", () => {
    const shared = { v: 1 };
    const root = { x: shared, y: shared };
    expect(serializeValue(root)).toBe('{"x":{"v":1},"y":{"v":1}}');
  });
});
