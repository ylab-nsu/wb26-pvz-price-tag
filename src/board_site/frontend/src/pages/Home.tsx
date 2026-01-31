import { useEffect, useState } from "react"

type Board = {
    id: number
    product: string
    base_price: number | ""
    discount: number | ""
    installed_at: string
    synced: boolean
    _errors?: Record<string, boolean>
}

const REFRESH_MINS = 3
const REFRESH_INTERVAL = REFRESH_MINS * 60 * 1000

export default function Home() {
    const [boards, setBoards] = useState<Board[]>([])
    const [originalBoards, setOriginalBoards] = useState<Board[]>([])

    const isEdited = (i: number) => {
        const b = boards[i]
        const orig = originalBoards[i]
        if (!orig) return false
        return (
            b.base_price !== orig.base_price ||
            b.discount !== orig.discount ||
            b.installed_at !== orig.installed_at ||
            b.product !== orig.product
        )
    }

    const fetchBoards = async () => {
        const res = await fetch("/api/boards")
        const data: Board[] = await res.json()
        setBoards(data)
        setOriginalBoards(data)
    }

    useEffect(() => {
        fetchBoards()
        const interval = setInterval(fetchBoards, REFRESH_INTERVAL)
        return () => clearInterval(interval)
    }, [])

    const updateBoard = (index: number, field: keyof Board, value: any) => {
        setBoards(prev => {
            const copy = [...prev]
            if (field === "base_price" || field === "discount") {
                copy[index] = { ...copy[index], [field]: value === "" ? "" : +value }
            } else {
                copy[index] = { ...copy[index], [field]: value }
            }
            if (copy[index]._errors?.[field]) {
                copy[index]._errors = { ...copy[index]._errors }
                delete copy[index]._errors[field]
            }
            return copy
        })
    }


    const validateBoard = (b: Board) => {
        const errors: Record<string, boolean> = {}
        if (!b.product || b.product.trim() === "") errors.product = true
        if (b.base_price === "" || b.base_price <= 0) errors.base_price = true
        if (b.discount === "" || b.discount < 0 || b.discount >= 100) errors.discount = true
        return errors
    }

    const applyChanges = async (index: number) => {
        const board = boards[index]
        const errors = validateBoard(board)

        if (Object.keys(errors).length > 0) {
            setBoards(prev => {
                const copy = [...prev]
                copy[index] = { ...copy[index], _errors: errors }
                return copy
            })
            return
        }

        try {
            const res = await fetch("/api/update_board", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(board),
            })

            if (!res.ok) throw new Error("Ошибка сервера")

            setOriginalBoards(prev => {
                const copy = [...prev]
                copy[index] = { ...board }
                return copy
            })

            setBoards(prev => {
                const copy = [...prev]
                copy[index] = { ...board, synced: false, _errors: {} }
                return copy
            })
        } catch (err) {
            console.error(err)
        }
    }


    return (
        <div className="page">
            <h1 className="page-title">Умные ценники</h1>

            <div className="table-card">
                <table>
                    <thead>
                        <tr>
                            <th>№</th>
                            <th>Товар</th>
                            <th>Цена</th>
                            <th>Скидка %</th>
                            <th>Дата установки</th>
                            <th>Статус</th>
                            <th></th>
                        </tr>
                    </thead>

                    <tbody>
                        {boards.map((b, i) => (
                            <tr key={b.id}>
                                <td className="id-cell">
                                    {b.id}
                                </td>

                                <td>
                                    <textarea
                                        className={`cell-input ${b._errors?.product ? "invalid" : ""}`}
                                        value={b.product}
                                        onChange={e => updateBoard(i, "product", e.target.value)}
                                        spellCheck={false}
                                    />
                                </td>

                                <td>
                                    <input
                                        type="number"
                                        className={`cell-input ${b._errors?.base_price ? "invalid" : ""}`}
                                        value={b.base_price === "" ? "" : b.base_price}
                                        onChange={e => updateBoard(i, "base_price", e.target.value)}
                                    />
                                </td>

                                <td>
                                    <input
                                        type="number"
                                        className={`cell-input ${b._errors?.discount ? "invalid" : ""}`}
                                        value={b.discount === "" ? "" : b.discount}
                                        onChange={e => updateBoard(i, "discount", e.target.value)}
                                    />
                                </td>

                                <td>
                                    <input
                                        type="date"
                                        className="cell-input"
                                        value={b.installed_at}
                                        onChange={e => updateBoard(i, "installed_at", e.target.value)}
                                    />
                                </td>

                                <td className={`status-cell ${b.synced ? "sync-ok" : "sync-wait"}`}>
                                    {b.synced ? "Обновлено" : "Обновление"}
                                </td>

                                <td>
                                    <button
                                        className={`apply-btn ${isEdited(i) ? "active" : "disabled"}`}
                                        disabled={!isEdited(i)}
                                        onClick={() => applyChanges(i)}
                                    >
                                        Применить
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    )
}
