import useComparison from '@/lib/comparison';

export default function CompareLink({ mobile=false }) {
    const { comparisons } = useComparison();

    return (
        <>
            <i className={"ci-compare mt-n1" + (mobile ? " text-muted me-2" : "")} />
            Сравнение
            { comparisons.length > 0 && (
                <span class="badge rounded-pill bg-primary ms-1 align-text-bottom">{ comparisons.length }</span>
            )}
        </>
    )
}
