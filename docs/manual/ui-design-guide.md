# Web UI デザインガイド

**Version**: 1.0
**対象**: デザイナー・フロントエンド開発者
**最終更新**: 2025-11-01

このドキュメントは、Reprospective Web UIのデザインをカスタマイズする際の参考資料です。各UIコンポーネントの実装場所と、変更方法を解説します。

---

## 目次

1. [UIアーキテクチャ概要](#uiアーキテクチャ概要)
2. [カラーシステム](#カラーシステム)
3. [コンポーネント別デザイン解説](#コンポーネント別デザイン解説)
4. [よくあるカスタマイズ例](#よくあるカスタマイズ例)
5. [トラブルシューティング](#トラブルシューティング)

---

## UIアーキテクチャ概要

### 技術スタック

- **React 19.2.0**: UIフレームワーク
- **Tailwind CSS v4**: CSSフレームワーク（ユーティリティファースト）
- **TypeScript 5.9.3**: 型安全な開発
- **Shadcn/ui**: 再利用可能なコンポーネントライブラリ（手動実装）

### ディレクトリ構造

```
services/web-ui/src/
├── components/
│   ├── common/          # 汎用コンポーネント（LoadingSpinner, ErrorMessage）
│   ├── directories/     # ディレクトリ管理画面のコンポーネント
│   ├── layout/          # レイアウトコンポーネント（Header, Layout）
│   └── ui/              # 基本UIコンポーネント（button, dialog, input等）
├── lib/
│   └── utils.ts         # ユーティリティ関数（cn()等）
├── index.css            # Tailwind CSS設定とグローバルスタイル
└── App.tsx              # アプリケーションのルートコンポーネント
```

### ファイルの役割

| ファイル | 役割 |
|---------|------|
| `index.css` | Tailwind CSS設定、カラー変数定義、グローバルスタイル |
| `components/layout/Layout.tsx` | ページ全体のレイアウト構造 |
| `components/layout/Header.tsx` | ヘッダー（タイトル、サブタイトル） |
| `components/directories/DirectoryList.tsx` | ディレクトリ一覧の表示とレイアウト |
| `components/directories/DirectoryCard.tsx` | 個別ディレクトリカードのデザイン |
| `components/directories/*Dialog.tsx` | モーダルダイアログ（追加・編集・削除） |
| `components/ui/*.tsx` | 再利用可能な基本UIコンポーネント |

---

## カラーシステム

### CSS変数（services/web-ui/src/index.css）

Tailwind CSS v4のカスタムカラー変数を使用しています。

```css
@theme {
  /* 背景色 */
  --color-background: #ffffff;        /* ページ背景 */
  --color-foreground: #09090b;        /* メインテキスト */

  /* カード */
  --color-card: #ffffff;              /* カード背景 */
  --color-card-foreground: #09090b;   /* カード内テキスト */

  /* プライマリカラー（メインアクション） */
  --color-primary: #2563eb;           /* プライマリボタン、リンク */
  --color-primary-foreground: #f8fafc;/* プライマリボタンのテキスト */

  /* セカンダリカラー（サブアクション） */
  --color-secondary: #f1f5f9;         /* セカンダリボタン背景 */
  --color-secondary-foreground: #0f172a; /* セカンダリボタンテキスト */

  /* ミュート（抑えめの要素） */
  --color-muted: #f1f5f9;             /* 無効な要素の背景 */
  --color-muted-foreground: #64748b;  /* 補足テキスト */

  /* アクセント（強調） */
  --color-accent: #f1f5f9;            /* アクセント背景 */
  --color-accent-foreground: #0f172a; /* アクセントテキスト */

  /* 破壊的アクション（削除等） */
  --color-destructive: #ef4444;       /* 削除ボタン等 */
  --color-destructive-foreground: #fef2f2; /* 削除ボタンテキスト */

  /* ボーダー */
  --color-border: #e2e8f0;            /* デフォルトのボーダー色 */
  --color-input: #e2e8f0;             /* 入力フィールドのボーダー */

  /* リング（フォーカス時の枠） */
  --color-ring: #2563eb;              /* フォーカス時のリング */
}
```

### カラー変更方法

**方法1: CSS変数を変更（推奨）**

`services/web-ui/src/index.css`の`@theme`セクション内の変数を変更すると、全体のカラーテーマが変更されます。

例: プライマリカラーを緑に変更
```css
--color-primary: #10b981;           /* 青 → 緑 */
--color-primary-foreground: #f0fdf4;
```

**方法2: Tailwindクラスを直接変更**

個別コンポーネント内でTailwindクラスを変更することも可能です。

例: ボタンの背景色を変更
```tsx
// 変更前
className="bg-primary text-primary-foreground"

// 変更後（具体的な色を指定）
className="bg-blue-600 text-white"
```

### 特殊ケース: インラインスタイル

**DirectoryCard.tsx**のボーダー色は、Tailwind CSS v4のカラークラスの競合により、インラインスタイルで実装されています。

```tsx
// services/web-ui/src/components/directories/DirectoryCard.tsx:44-46
style={{
  border: directory.enabled ? '2px solid #BFDBFE' : '2px solid #D1D5DB'
}}
```

**変更方法**: `#BFDBFE`（青）、`#D1D5DB`（グレー）を任意の16進カラーコードに変更してください。

例: 緑とグレーに変更
```tsx
style={{
  border: directory.enabled ? '2px solid #A7F3D0' : '2px solid #D1D5DB'
}}
```

---

## コンポーネント別デザイン解説

### 1. ヘッダー（Header.tsx）

**ファイル**: `services/web-ui/src/components/layout/Header.tsx`

#### 現在のデザイン

```tsx
<header className="border-b bg-background">
  <div className="container mx-auto px-4 py-4 flex items-center gap-3">
    <Folder className="h-8 w-8 text-primary" />
    <div>
      <h1 className="text-2xl font-bold">Reprospective</h1>
      <p className="text-sm text-muted-foreground">
        ファイルシステム監視設定
      </p>
    </div>
  </div>
</header>
```

#### カスタマイズ可能な箇所

| 要素 | 現在の設定 | 変更例 |
|------|-----------|--------|
| **ヘッダー高さ** | `py-4` (1rem上下) | `py-6` → より高く、`py-2` → より低く |
| **タイトルサイズ** | `text-2xl` (1.5rem) | `text-3xl` → より大きく、`text-xl` → より小さく |
| **タイトルフォント** | `font-bold` (700) | `font-black` (900) → より太く |
| **サブタイトルサイズ** | `text-sm` (0.875rem) | `text-base` → より大きく、`text-xs` → より小さく |
| **サブタイトル色** | `text-muted-foreground` | `text-gray-600` → 具体的な色指定 |
| **アイコンサイズ** | `h-8 w-8` (2rem) | `h-10 w-10` → より大きく |
| **アイコン色** | `text-primary` | `text-blue-600` → 具体的な色指定 |
| **ボーダー** | `border-b` | `border-b-2` → より太く |
| **背景色** | `bg-background` | `bg-gray-50` → グレー背景 |

**例: より目立つヘッダーに変更**

```tsx
<header className="border-b-2 bg-gradient-to-r from-blue-50 to-indigo-50">
  <div className="container mx-auto px-4 py-6 flex items-center gap-4">
    <Folder className="h-10 w-10 text-blue-600" />
    <div>
      <h1 className="text-3xl font-black text-gray-900">Reprospective</h1>
      <p className="text-base text-gray-600">
        ファイルシステム監視設定
      </p>
    </div>
  </div>
</header>
```

---

### 2. ディレクトリカード（DirectoryCard.tsx）

**ファイル**: `services/web-ui/src/components/directories/DirectoryCard.tsx`

#### 現在のデザイン

```tsx
<div
  className={cn(
    'rounded-lg p-6 shadow-md hover:shadow-lg transition-all',
    directory.enabled ? 'bg-white' : 'bg-gray-50 opacity-60'
  )}
  style={{
    border: directory.enabled ? '2px solid #BFDBFE' : '2px solid #D1D5DB'
  }}
>
  {/* カード内容 */}
</div>
```

#### カスタマイズ可能な箇所

| 要素 | 現在の設定 | 変更例 |
|------|-----------|--------|
| **角丸** | `rounded-lg` (0.5rem) | `rounded-xl` → より丸く、`rounded-md` → より角ばる |
| **内部余白** | `p-6` (1.5rem) | `p-8` → より広く、`p-4` → より狭く |
| **影** | `shadow-md` | `shadow-lg` → より深い影、`shadow-sm` → より浅い影 |
| **ホバー時の影** | `hover:shadow-lg` | `hover:shadow-xl` → より深い影 |
| **有効時の背景** | `bg-white` | `bg-blue-50` → 薄い青背景 |
| **無効時の背景** | `bg-gray-50` | `bg-gray-100` → より濃いグレー |
| **無効時の透明度** | `opacity-60` | `opacity-50` → より薄く、`opacity-70` → より濃く |
| **ボーダー色（有効）** | `#BFDBFE` (blue-200) | `#93C5FD` → より濃い青 |
| **ボーダー色（無効）** | `#D1D5DB` (gray-300) | `#9CA3AF` → より濃いグレー |
| **ボーダー太さ** | `2px` | `3px` → より太く、`1px` → より細く |

#### アイコンとテキスト（DirectoryCard.tsx:50-81）

```tsx
<div className="flex gap-3 flex-1 min-w-0">
  <Folder
    className={cn(
      'h-5 w-5 mt-0.5 flex-shrink-0',
      directory.enabled ? 'text-primary' : 'text-muted-foreground'
    )}
  />
  <div className="flex-1 min-w-0">
    <h3 className="font-semibold text-lg truncate">
      {directory.display_name || directory.directory_path.split('/').pop()}
    </h3>
    <p className="text-sm text-muted-foreground truncate" title={directory.directory_path}>
      {directory.directory_path}
    </p>
    {directory.description && (
      <p className="text-sm text-muted-foreground mt-2">
        {directory.description}
      </p>
    )}
    <div className="flex gap-4 mt-3 text-xs text-muted-foreground">
      <span>ID: {directory.id}</span>
      <span>
        作成: {new Date(directory.created_at).toLocaleDateString('ja-JP')}
      </span>
      {directory.enabled && (
        <span className="text-green-600 font-semibold">● 監視中</span>
      )}
      {!directory.enabled && (
        <span className="text-muted-foreground">● 無効</span>
      )}
    </div>
  </div>
</div>
```

| 要素 | 現在の設定 | 変更例 |
|------|-----------|--------|
| **アイコンサイズ** | `h-5 w-5` (1.25rem) | `h-6 w-6` → より大きく |
| **アイコン色（有効）** | `text-primary` | `text-blue-600` → 具体的な色 |
| **アイコン色（無効）** | `text-muted-foreground` | `text-gray-400` → 具体的な色 |
| **タイトルサイズ** | `text-lg` (1.125rem) | `text-xl` → より大きく |
| **タイトルフォント** | `font-semibold` (600) | `font-bold` (700) → より太く |
| **パスのサイズ** | `text-sm` (0.875rem) | `text-base` → より大きく |
| **パスの色** | `text-muted-foreground` | `text-gray-500` → 具体的な色 |
| **説明文のサイズ** | `text-sm` | `text-base` → より大きく |
| **説明文の上余白** | `mt-2` (0.5rem) | `mt-3` → より広く |
| **ステータス表示サイズ** | `text-xs` (0.75rem) | `text-sm` → より大きく |
| **監視中の色** | `text-green-600` | `text-emerald-600` → より鮮やかな緑 |

#### アクションボタン（DirectoryCard.tsx:85-118）

```tsx
<div className="flex gap-2 flex-shrink-0">
  <button
    onClick={handleToggle}
    disabled={isToggling}
    className={cn(
      'p-3 rounded-md transition-all border',
      directory.enabled
        ? 'hover:bg-yellow-50 text-yellow-700 border-yellow-200 hover:border-yellow-300'
        : 'hover:bg-green-50 text-green-700 border-green-200 hover:border-green-300',
      isToggling && 'opacity-50 cursor-not-allowed'
    )}
    title={directory.enabled ? '監視を無効化' : '監視を有効化'}
  >
    {directory.enabled ? (
      <PowerOff className="h-5 w-5" />
    ) : (
      <Power className="h-5 w-5" />
    )}
  </button>
  <button
    onClick={() => onEdit(directory)}
    className="p-3 rounded-md hover:bg-blue-50 text-blue-700 border border-blue-200 hover:border-blue-300 transition-all"
    title="編集"
  >
    <Edit className="h-5 w-5" />
  </button>
  <button
    onClick={() => onDelete(directory)}
    className="p-3 rounded-md hover:bg-red-50 text-red-700 border border-red-200 hover:border-red-300 transition-all"
    title="削除"
  >
    <Trash2 className="h-5 w-5" />
  </button>
</div>
```

| 要素 | 現在の設定 | 変更例 |
|------|-----------|--------|
| **ボタン間隔** | `gap-2` (0.5rem) | `gap-3` → より広く、`gap-1` → より狭く |
| **ボタン内余白** | `p-3` (0.75rem) | `p-4` → より大きく、`p-2` → より小さく |
| **ボタン角丸** | `rounded-md` (0.375rem) | `rounded-lg` → より丸く、`rounded` → より角ばる |
| **アイコンサイズ** | `h-5 w-5` (1.25rem) | `h-6 w-6` → より大きく |
| **トグルボタン（有効時）背景** | `hover:bg-yellow-50` | `hover:bg-orange-50` → オレンジ |
| **トグルボタン（有効時）テキスト** | `text-yellow-700` | `text-orange-700` → オレンジ |
| **トグルボタン（有効時）ボーダー** | `border-yellow-200` | `border-orange-200` → オレンジ |
| **トグルボタン（無効時）背景** | `hover:bg-green-50` | `hover:bg-emerald-50` → より鮮やかな緑 |
| **編集ボタン背景** | `hover:bg-blue-50` | `hover:bg-sky-50` → 明るい青 |
| **削除ボタン背景** | `hover:bg-red-50` | `hover:bg-rose-50` → より鮮やかな赤 |

**例: より大きく目立つボタンに変更**

```tsx
<div className="flex gap-3 flex-shrink-0">
  <button
    className={cn(
      'p-4 rounded-lg transition-all border-2',
      directory.enabled
        ? 'hover:bg-orange-50 text-orange-700 border-orange-300 hover:border-orange-400'
        : 'hover:bg-emerald-50 text-emerald-700 border-emerald-300 hover:border-emerald-400',
      isToggling && 'opacity-50 cursor-not-allowed'
    )}
  >
    {directory.enabled ? (
      <PowerOff className="h-6 w-6" />
    ) : (
      <Power className="h-6 w-6" />
    )}
  </button>
  {/* 他のボタンも同様に変更 */}
</div>
```

---

### 3. ディレクトリ一覧（DirectoryList.tsx）

**ファイル**: `services/web-ui/src/components/directories/DirectoryList.tsx`

#### ヘッダー部分（DirectoryList.tsx:48-62）

```tsx
<div className="flex items-center justify-between">
  <div>
    <h2 className="text-2xl font-bold">監視対象ディレクトリ</h2>
    <p className="text-sm text-muted-foreground mt-1">
      ファイルシステム監視の対象ディレクトリを管理します
    </p>
  </div>
  <button
    onClick={() => setIsAddDialogOpen(true)}
    className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
  >
    <Plus className="h-4 w-4" />
    新規追加
  </button>
</div>
```

| 要素 | 現在の設定 | 変更例 |
|------|-----------|--------|
| **見出しサイズ** | `text-2xl` (1.5rem) | `text-3xl` → より大きく |
| **見出しフォント** | `font-bold` (700) | `font-black` (900) → より太く |
| **説明文サイズ** | `text-sm` (0.875rem) | `text-base` → より大きく |
| **説明文の上余白** | `mt-1` (0.25rem) | `mt-2` → より広く |
| **追加ボタン横余白** | `px-4` (1rem) | `px-6` → より広く |
| **追加ボタン縦余白** | `py-2` (0.5rem) | `py-3` → より高く |
| **追加ボタン角丸** | `rounded-md` (0.375rem) | `rounded-lg` → より丸く |
| **追加ボタン背景** | `bg-primary` | `bg-blue-600` → 具体的な色 |
| **追加ボタンテキスト** | `text-primary-foreground` | `text-white` → 具体的な色 |
| **アイコンサイズ** | `h-4 w-4` (1rem) | `h-5 w-5` → より大きく |

#### カード一覧レイアウト（DirectoryList.tsx:78-87）

```tsx
<div className="grid gap-6">
  {directories.map((directory) => (
    <DirectoryCard
      key={directory.id}
      directory={directory}
      onEdit={setEditingDirectory}
      onDelete={setDeletingDirectory}
    />
  ))}
</div>
```

| 要素 | 現在の設定 | 変更例 |
|------|-----------|--------|
| **カード間隔** | `gap-6` (1.5rem) | `gap-8` → より広く、`gap-4` → より狭く |
| **レイアウト** | `grid` (1カラム) | `grid grid-cols-2 gap-4` → 2カラム表示 |

**例: 2カラムレイアウトに変更**

```tsx
<div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
  {directories.map((directory) => (
    <DirectoryCard
      key={directory.id}
      directory={directory}
      onEdit={setEditingDirectory}
      onDelete={setDeletingDirectory}
    />
  ))}
</div>
```

`lg:grid-cols-2`は、大画面（1024px以上）で2カラム、それ以下では1カラムを意味します。

#### 空状態表示（DirectoryList.tsx:66-76）

```tsx
<div className="text-center py-12 border-2 border-dashed rounded-lg">
  <p className="text-muted-foreground">
    監視対象ディレクトリが登録されていません
  </p>
  <button
    onClick={() => setIsAddDialogOpen(true)}
    className="mt-4 text-primary hover:underline"
  >
    最初のディレクトリを追加
  </button>
</div>
```

| 要素 | 現在の設定 | 変更例 |
|------|-----------|--------|
| **縦余白** | `py-12` (3rem) | `py-16` → より高く、`py-8` → より低く |
| **ボーダー太さ** | `border-2` (2px) | `border-4` → より太く |
| **ボーダー種類** | `border-dashed` | `border-dotted` → 点線 |
| **角丸** | `rounded-lg` (0.5rem) | `rounded-xl` → より丸く |
| **テキスト色** | `text-muted-foreground` | `text-gray-500` → 具体的な色 |
| **リンクボタン上余白** | `mt-4` (1rem) | `mt-6` → より広く |
| **リンクボタン色** | `text-primary` | `text-blue-600` → 具体的な色 |

---

### 4. ダイアログ（Dialog系コンポーネント）

**ファイル**:
- `services/web-ui/src/components/directories/AddDirectoryDialog.tsx`
- `services/web-ui/src/components/directories/EditDirectoryDialog.tsx`
- `services/web-ui/src/components/directories/DeleteDirectoryDialog.tsx`

#### ダイアログヘッダー（AddDirectoryDialog.tsx:85-91）

```tsx
<DialogHeader>
  <DialogTitle>ディレクトリを追加</DialogTitle>
  <DialogDescription>
    監視対象の新しいディレクトリを追加します。
    絶対パスで指定してください。
  </DialogDescription>
</DialogHeader>
```

**DialogTitle**と**DialogDescription**のスタイルは`services/web-ui/src/components/ui/dialog.tsx`で定義されています。

```tsx
// dialog.tsx:73-78
const DialogTitle = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Title>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Title>
>(({ className, ...props }, ref) => (
  <DialogPrimitive.Title
    ref={ref}
    className={cn(
      'text-lg font-semibold leading-none tracking-tight',
      className
    )}
    {...props}
  />
));

// dialog.tsx:86-94
const DialogDescription = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Description>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Description>
>(({ className, ...props }, ref) => (
  <DialogPrimitive.Description
    ref={ref}
    className={cn('text-sm text-muted-foreground', className)}
    {...props}
  />
));
```

| 要素 | 現在の設定 | 変更方法 |
|------|-----------|---------|
| **タイトルサイズ** | `text-lg` (1.125rem) | `dialog.tsx`の`text-lg`を`text-xl`等に変更 |
| **タイトルフォント** | `font-semibold` (600) | `dialog.tsx`の`font-semibold`を`font-bold`等に変更 |
| **説明文サイズ** | `text-sm` (0.875rem) | `dialog.tsx`の`text-sm`を`text-base`等に変更 |
| **説明文色** | `text-muted-foreground` | `dialog.tsx`の`text-muted-foreground`を変更 |

#### フォームフィールド（AddDirectoryDialog.tsx:92-159）

```tsx
<div className="space-y-4 py-4">
  {/* ディレクトリパス */}
  <div className="space-y-2">
    <Label htmlFor="path">ディレクトリパス *</Label>
    <Input
      id="path"
      placeholder="/home/user/documents"
      {...register('directory_path')}
      disabled={isSubmitting}
    />
    {errors.directory_path && (
      <p className="text-sm text-destructive">
        {errors.directory_path.message}
      </p>
    )}
  </div>
  {/* 他のフィールド... */}
</div>
```

| 要素 | 現在の設定 | 変更例 |
|------|-----------|--------|
| **フィールド間隔** | `space-y-4` (1rem) | `space-y-6` → より広く、`space-y-3` → より狭く |
| **フォーム上下余白** | `py-4` (1rem) | `py-6` → より広く |
| **ラベルと入力欄の間隔** | `space-y-2` (0.5rem) | `space-y-3` → より広く |
| **エラーメッセージサイズ** | `text-sm` (0.875rem) | `text-xs` → より小さく |
| **エラーメッセージ色** | `text-destructive` | `text-red-600` → 具体的な色 |

**Label**と**Input**のスタイルは以下で定義されています:

```tsx
// services/web-ui/src/components/ui/label.tsx:9-18
const Label = React.forwardRef<
  React.ElementRef<typeof LabelPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof LabelPrimitive.Root> &
    VariantProps<typeof labelVariants>
>(({ className, ...props }, ref) => (
  <LabelPrimitive.Root
    ref={ref}
    className={cn(labelVariants(), className)}
    {...props}
  />
));

const labelVariants = cva(
  'text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70'
);

// services/web-ui/src/components/ui/input.tsx:8-20
const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-base ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-foreground placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 md:text-sm',
          className
        )}
        ref={ref}
        {...props}
      />
    );
  }
);
```

| 要素 | 現在の設定 | 変更方法 |
|------|-----------|---------|
| **ラベルサイズ** | `text-sm` (0.875rem) | `label.tsx`の`text-sm`を変更 |
| **ラベルフォント** | `font-medium` (500) | `label.tsx`の`font-medium`を変更 |
| **入力欄高さ** | `h-10` (2.5rem) | `input.tsx`の`h-10`を`h-12`等に変更 |
| **入力欄横余白** | `px-3` (0.75rem) | `input.tsx`の`px-3`を変更 |
| **入力欄縦余白** | `py-2` (0.5rem) | `input.tsx`の`py-2`を変更 |
| **入力欄角丸** | `rounded-md` (0.375rem) | `input.tsx`の`rounded-md`を変更 |
| **入力欄ボーダー色** | `border-input` | `input.tsx`の`border-input`を変更 |
| **フォーカス時リング色** | `ring-ring` | `input.tsx`の`ring-ring`を変更 |

#### ダイアログボタン（AddDirectoryDialog.tsx:160-175）

```tsx
<DialogFooter>
  <Button
    type="button"
    variant="outline"
    onClick={() => onOpenChange(false)}
    disabled={isSubmitting}
  >
    キャンセル
  </Button>
  <Button type="submit" disabled={isSubmitting}>
    {isSubmitting ? (
      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
    ) : null}
    追加
  </Button>
</DialogFooter>
```

**Button**のスタイルは`services/web-ui/src/components/ui/button.tsx`で定義されています。

```tsx
// button.tsx:6-41
const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0',
  {
    variants: {
      variant: {
        default: 'bg-primary text-primary-foreground hover:bg-primary/90',
        destructive:
          'bg-destructive text-destructive-foreground hover:bg-destructive/90',
        outline:
          'border border-input bg-background hover:bg-accent hover:text-accent-foreground',
        secondary:
          'bg-secondary text-secondary-foreground hover:bg-secondary/80',
        ghost: 'hover:bg-accent hover:text-accent-foreground',
        link: 'text-primary underline-offset-4 hover:underline',
      },
      size: {
        default: 'h-10 px-4 py-2',
        sm: 'h-9 rounded-md px-3',
        lg: 'h-11 rounded-md px-8',
        icon: 'h-10 w-10',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
);
```

| Variant | 説明 | 使用場所 |
|---------|------|---------|
| `default` | プライマリボタン（青） | 追加・保存ボタン |
| `destructive` | 削除ボタン（赤） | 削除確認ダイアログ |
| `outline` | アウトラインボタン | キャンセルボタン |
| `secondary` | セカンダリボタン | - |
| `ghost` | 背景なしボタン | - |
| `link` | リンクスタイルボタン | - |

| Size | 説明 |
|------|------|
| `default` | 通常サイズ（h-10） |
| `sm` | 小サイズ（h-9） |
| `lg` | 大サイズ（h-11） |
| `icon` | アイコンボタン（h-10 w-10） |

**変更例: ボタンを大きくする**

```tsx
<Button type="submit" disabled={isSubmitting} size="lg">
  {isSubmitting ? (
    <Loader2 className="mr-2 h-5 w-5 animate-spin" />
  ) : null}
  追加
</Button>
```

または、`button.tsx`の`lg`サイズを変更:

```tsx
// button.tsx:35
lg: 'h-12 rounded-lg px-10',  // 高さと横幅を増やす
```

---

### 5. 共通UIコンポーネント

#### LoadingSpinner（LoadingSpinner.tsx）

**ファイル**: `services/web-ui/src/components/common/LoadingSpinner.tsx`

```tsx
<div className="flex flex-col items-center justify-center gap-3">
  <Loader2 className="h-8 w-8 animate-spin text-primary" />
  {text && <p className="text-sm text-muted-foreground">{text}</p>}
</div>
```

| 要素 | 現在の設定 | 変更例 |
|------|-----------|--------|
| **スピナーとテキストの間隔** | `gap-3` (0.75rem) | `gap-4` → より広く |
| **スピナーサイズ（lg）** | `h-8 w-8` (2rem) | `h-10 w-10` → より大きく |
| **スピナー色** | `text-primary` | `text-blue-600` → 具体的な色 |
| **テキストサイズ** | `text-sm` (0.875rem) | `text-base` → より大きく |

#### ErrorMessage（ErrorMessage.tsx）

**ファイル**: `services/web-ui/src/components/common/ErrorMessage.tsx`

```tsx
<div className="rounded-lg border-2 border-destructive/50 bg-destructive/10 p-6">
  <div className="flex items-start gap-3">
    <AlertCircle className="h-5 w-5 text-destructive flex-shrink-0 mt-0.5" />
    <div className="flex-1">
      <h3 className="font-semibold text-destructive mb-1">{title}</h3>
      <p className="text-sm text-destructive/90">{message}</p>
    </div>
  </div>
</div>
```

| 要素 | 現在の設定 | 変更例 |
|------|-----------|--------|
| **角丸** | `rounded-lg` (0.5rem) | `rounded-xl` → より丸く |
| **ボーダー太さ** | `border-2` (2px) | `border-4` → より太く |
| **ボーダー色** | `border-destructive/50` | `border-red-300` → 具体的な色 |
| **背景色** | `bg-destructive/10` | `bg-red-50` → 具体的な色 |
| **内余白** | `p-6` (1.5rem) | `p-8` → より広く |
| **アイコンサイズ** | `h-5 w-5` (1.25rem) | `h-6 w-6` → より大きく |
| **アイコン色** | `text-destructive` | `text-red-600` → 具体的な色 |
| **タイトルフォント** | `font-semibold` (600) | `font-bold` (700) → より太く |
| **タイトル色** | `text-destructive` | `text-red-700` → 具体的な色 |
| **メッセージサイズ** | `text-sm` (0.875rem) | `text-base` → より大きく |
| **メッセージ色** | `text-destructive/90` | `text-red-600` → 具体的な色 |

---

## よくあるカスタマイズ例

### 1. テーマ全体の色を変更する

**青 → 緑に変更する場合**

`services/web-ui/src/index.css`を編集:

```css
@theme {
  --color-primary: #10b981;           /* 緑 */
  --color-primary-foreground: #f0fdf4;

  --color-ring: #10b981;              /* フォーカス時のリングも緑に */
}
```

また、**DirectoryCard.tsx**のボーダー色も変更:

```tsx
// DirectoryCard.tsx:44-46
style={{
  border: directory.enabled ? '2px solid #A7F3D0' : '2px solid #D1D5DB'
}}
```

### 2. カード全体を大きくする

`services/web-ui/src/components/directories/DirectoryCard.tsx`を編集:

```tsx
// 変更前
<div
  className={cn(
    'rounded-lg p-6 shadow-md hover:shadow-lg transition-all',
    // ...
  )}
>

// 変更後（より大きく）
<div
  className={cn(
    'rounded-xl p-8 shadow-lg hover:shadow-xl transition-all',
    // ...
  )}
>
```

```tsx
// アイコンとテキストのサイズも大きく
<Folder className={cn('h-6 w-6 mt-0.5 flex-shrink-0', ...)} />
<h3 className="font-bold text-xl truncate">...</h3>
<p className="text-base text-muted-foreground truncate">...</p>
```

```tsx
// ボタンも大きく
<button className="p-4 rounded-lg ...">
  <Edit className="h-6 w-6" />
</button>
```

### 3. ディレクトリ一覧を2カラム表示にする

`services/web-ui/src/components/directories/DirectoryList.tsx`を編集:

```tsx
// 変更前
<div className="grid gap-6">

// 変更後（大画面で2カラム）
<div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
```

### 4. ヘッダーを目立たせる

`services/web-ui/src/components/layout/Header.tsx`を編集:

```tsx
// 変更前
<header className="border-b bg-background">
  <div className="container mx-auto px-4 py-4 flex items-center gap-3">
    <Folder className="h-8 w-8 text-primary" />
    <div>
      <h1 className="text-2xl font-bold">Reprospective</h1>
      <p className="text-sm text-muted-foreground">
        ファイルシステム監視設定
      </p>
    </div>
  </div>
</header>

// 変更後（グラデーション背景、より大きく）
<header className="border-b-2 bg-gradient-to-r from-blue-50 to-indigo-50 shadow-sm">
  <div className="container mx-auto px-6 py-6 flex items-center gap-4">
    <Folder className="h-10 w-10 text-blue-600" />
    <div>
      <h1 className="text-3xl font-black text-gray-900">Reprospective</h1>
      <p className="text-base text-gray-600">
        ファイルシステム監視設定
      </p>
    </div>
  </div>
</header>
```

### 5. ボタンのサイズを統一して大きくする

`services/web-ui/src/components/ui/button.tsx`を編集:

```tsx
// buttonVariants の size.default を変更
size: {
  default: 'h-12 px-6 py-3',  // より大きく
  sm: 'h-10 rounded-md px-4',
  lg: 'h-14 rounded-lg px-10',
  icon: 'h-12 w-12',
},
```

### 6. ダイアログのタイトルを大きくする

`services/web-ui/src/components/ui/dialog.tsx`を編集:

```tsx
// DialogTitle のクラス名を変更
className={cn(
  'text-xl font-bold leading-none tracking-tight',  // text-lg → text-xl, font-semibold → font-bold
  className
)}
```

### 7. フォーム入力欄を大きくする

`services/web-ui/src/components/ui/input.tsx`を編集:

```tsx
className={cn(
  'flex h-12 w-full rounded-lg border border-input bg-background px-4 py-3 text-base ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-foreground placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
  // h-10 → h-12, rounded-md → rounded-lg, px-3 → px-4, py-2 → py-3
  className
)}
```

---

## トラブルシューティング

### Q1: Tailwindのカラークラスが効かない

**原因**: Tailwind CSS v4ではカスタムカラー変数を使用しているため、`bg-blue-200`のようなデフォルトカラークラスが動作しない場合があります。

**解決策**:
1. CSS変数を使用する: `bg-primary`, `text-primary-foreground`
2. 具体的な色を指定する: `bg-blue-600`, `text-white`
3. インラインスタイルを使用する: `style={{ backgroundColor: '#3B82F6' }}`

### Q2: 変更がブラウザに反映されない

**原因**: Viteの開発サーバーのキャッシュ、またはブラウザキャッシュ

**解決策**:
1. ブラウザのハードリロード: `Ctrl + Shift + R` (Linux/Windows), `Cmd + Shift + R` (Mac)
2. Vite開発サーバーの再起動:
   ```bash
   docker compose restart web-ui
   ```
3. ブラウザのキャッシュクリア

### Q3: ビルドエラーが発生する

**原因**: TypeScriptの型エラー、または構文エラー

**解決策**:
1. エラーメッセージを確認:
   ```bash
   docker compose logs web-ui
   ```
2. 型エラーの場合、適切な型を指定:
   ```tsx
   // エラー例: Type 'string | undefined' is not assignable to type 'string'

   // 修正前
   const name: string = directory.display_name;

   // 修正後
   const name: string = directory.display_name || '';
   ```
3. インポートエラーの場合、パスエイリアスを確認:
   ```tsx
   // 正しい
   import { cn } from '@/lib/utils';

   // 間違い
   import { cn } from '../lib/utils';
   ```

### Q4: ボーダーが表示されない

**原因**: Tailwind CSS v4のカスタムカラー変数との競合

**解決策**: インラインスタイルを使用
```tsx
style={{
  border: '2px solid #BFDBFE'
}}
```

### Q5: レスポンシブデザインがうまく動作しない

**原因**: Tailwindのブレークポイント指定が不適切

**解決策**:
```tsx
// Tailwindのブレークポイント
// sm: 640px
// md: 768px
// lg: 1024px
// xl: 1280px
// 2xl: 1536px

// 例: 小画面では1カラム、大画面では2カラム
<div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
```

### Q6: ダイアログが表示されない

**原因**: `open`プロパティが正しく渡されていない

**解決策**:
```tsx
// AddDirectoryDialog.tsx等で確認
<Dialog open={open} onOpenChange={onOpenChange}>
```

親コンポーネントから`open`と`onOpenChange`が正しく渡されているか確認してください。

---

## まとめ

### デザイン変更の基本フロー

1. **何を変更したいか明確にする**（色、サイズ、配置等）
2. **該当するコンポーネントを特定する**（このドキュメントの「コンポーネント別デザイン解説」を参照）
3. **変更方法を選択する**:
   - 全体的な変更 → `index.css`のCSS変数を変更
   - 個別の変更 → 該当コンポーネントのTailwindクラスを変更
   - ボーダー等の特殊ケース → インラインスタイルを使用
4. **変更を適用して確認**:
   ```bash
   # ブラウザでハードリロード: Ctrl + Shift + R
   # または開発サーバーを再起動
   docker compose restart web-ui
   ```

### 推奨される変更順序

1. **カラーテーマ全体** → `index.css`のCSS変数
2. **レイアウト（カード間隔、2カラム化等）** → `DirectoryList.tsx`
3. **カードデザイン** → `DirectoryCard.tsx`
4. **ボタンサイズ** → `button.tsx`
5. **入力フォーム** → `input.tsx`, `label.tsx`
6. **その他細かい調整** → 各コンポーネント

### 参考リンク

- **Tailwind CSS公式ドキュメント**: https://tailwindcss.com/docs
- **Radix UI（ダイアログ等の基盤）**: https://www.radix-ui.com/
- **Lucide Icons（アイコンライブラリ）**: https://lucide.dev/

---

**ご質問やサポートが必要な場合は、開発チームまでお問い合わせください。**
